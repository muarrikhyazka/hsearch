#!/bin/bash

# HSSearch Data Import Script
# Handles all data import and database operations
# Usage: ./import-data.sh [--status|--force|--help]

set -e

echo "📊 HSSearch Data Import Manager"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --status    Check current data status"
    echo "  --force     Force reimport even if data exists"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Import data (skip if exists)"
    echo "  $0 --status     # Check data status"
    echo "  $0 --force      # Force reimport data"
}

# Parse command line arguments
FORCE_IMPORT=false
STATUS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_IMPORT=true
            shift
            ;;
        --status)
            STATUS_ONLY=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if Docker containers are running
check_containers() {
    print_status "Checking Docker containers..."
    
    if ! docker compose ps | grep -q "postgres.*Up"; then
        print_error "PostgreSQL container is not running"
        print_status "Please start the application first: ./deploy-app.sh"
        exit 1
    fi
    
    if ! docker compose ps | grep -q "backend.*Up"; then
        print_error "Backend container is not running"
        print_status "Please start the application first: ./deploy-app.sh"
        exit 1
    fi
    
    print_success "Required containers are running"
}

# Check database connectivity
check_database() {
    print_status "Testing database connection..."
    
    if docker compose exec -T postgres pg_isready -U hsearch_user -d hsearch_db > /dev/null; then
        print_success "Database connection successful"
    else
        print_error "Cannot connect to database"
        print_status "Checking database logs..."
        docker compose logs postgres | tail -20
        exit 1
    fi
}

# Get current data status
get_data_status() {
    print_status "Checking current data status..."
    
    # Check if table exists
    table_exists=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'hs_codes';" 2>/dev/null | tr -d ' \n' || echo "0")
    
    if [ "$table_exists" -eq 0 ]; then
        echo "  • Table Status: ❌ Not created"
        echo "  • Record Count: 0"
        echo "  • Data Status: No data"
        return 1
    fi
    
    # Get record count
    record_count=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM hs_codes;" 2>/dev/null | tr -d ' \n' || echo "0")
    
    echo "  • Table Status: ✅ Exists"
    echo "  • Record Count: $record_count"
    
    if [ "$record_count" -gt 0 ]; then
        # Check Indonesian translations
        indonesian_count=$(docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -t -c "SELECT COUNT(*) FROM hs_codes WHERE description_id IS NOT NULL AND description_id != '';" 2>/dev/null | tr -d ' \n' || echo "0")
        
        echo "  • Indonesian Translations: $indonesian_count"
        
        if [ "$indonesian_count" -gt 0 ]; then
            translation_percent=$(( indonesian_count * 100 / record_count ))
            echo "  • Translation Coverage: ${translation_percent}%"
        fi
        
        # Show sample data
        print_status "Sample data:"
        docker compose exec -T postgres psql -U hsearch_user -d hsearch_db -c "SELECT hs_code, LEFT(description_en, 40) as description, category FROM hs_codes LIMIT 3;" 2>/dev/null || true
        
        echo "  • Data Status: ✅ Ready"
        return 0
    else
        echo "  • Data Status: ❌ Empty"
        return 1
    fi
}

# Check if data file exists
check_data_file() {
    print_status "Checking data file availability..."
    
    if [ ! -f "data/final-dataset-retranslated.csv" ]; then
        print_error "Data file not found: data/final-dataset-retranslated.csv"
        print_status "Available data files:"
        ls -la data/*.csv 2>/dev/null || echo "No CSV files found in data/ directory"
        exit 1
    fi
    
    # Check file size
    data_size=$(du -h data/final-dataset-retranslated.csv | cut -f1)
    print_success "Data file found: $data_size"
    
    # Check if backend container can access the file
    if docker compose exec -T backend test -f /app/data/final-dataset-retranslated.csv; then
        print_success "Data file accessible from backend container"
    else
        print_error "Data file not accessible from backend container"
        print_status "Checking data directory mount..."
        docker compose exec -T backend ls -la /app/data/ || print_error "Data directory not mounted"
        exit 1
    fi
}

# Perform data import
import_data() {
    print_status "Starting data import process..."
    print_warning "This process may take several minutes..."
    
    # Create a timestamp for this import
    import_start=$(date)
    
    print_status "Import started at: $import_start"
    print_status "Executing import script in backend container..."
    
    # Run the import script with output streaming
    if docker compose exec -T backend python /app/backend/import_data.py; then
        import_end=$(date)
        print_success "Data import completed successfully!"
        print_status "Import started: $import_start"
        print_status "Import finished: $import_end"
        
        # Get final statistics
        print_status "Getting final statistics..."
        get_data_status
        
    else
        print_error "Data import failed!"
        print_status "Checking backend logs for errors..."
        docker compose logs backend | tail -50
        exit 1
    fi
}

# Verify import success
verify_import() {
    print_status "Verifying import success..."
    
    # Test API endpoint
    if curl -s http://localhost:5000/api/health | grep -q "healthy"; then
        print_success "Backend API is responding"
    else
        print_warning "Backend API not responding properly"
    fi
    
    # Test search functionality
    print_status "Testing search functionality..."
    search_result=$(curl -s -X POST http://localhost:5000/api/search -H "Content-Type: application/json" -d '{"query": "horse", "limit": 1}' | grep -o '"results":\[.*\]' || echo "")
    
    if [ ! -z "$search_result" ]; then
        print_success "Search functionality is working"
    else
        print_warning "Search might not be working properly"
    fi
}

# Main execution
main() {
    echo "Starting data import process..."
    echo ""
    
    # Always check containers and database
    check_containers
    check_database
    
    # If status only, show status and exit
    if [ "$STATUS_ONLY" = true ]; then
        get_data_status
        exit 0
    fi
    
    # Check current data status
    echo ""
    print_status "Current Data Status:"
    if get_data_status && [ "$FORCE_IMPORT" = false ]; then
        echo ""
        print_success "Data already exists and appears complete"
        print_warning "Use --force to reimport data anyway"
        print_status "Or use --status to check data status"
        exit 0
    fi
    
    # Check data file
    echo ""
    check_data_file
    
    # Ask for confirmation if forcing reimport
    if [ "$FORCE_IMPORT" = true ]; then
        echo ""
        print_warning "⚠️  FORCE REIMPORT REQUESTED"
        print_warning "This will replace all existing data!"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Import cancelled"
            exit 0
        fi
    fi
    
    # Perform import
    echo ""
    import_data
    
    # Verify import
    echo ""
    verify_import
    
    echo ""
    print_success "🎉 Data import process completed!"
    print_status "Your HSSearch system is ready with complete HS codes data"
    print_status "Access your system at: http://localhost"
}

# Run main function
main "$@"