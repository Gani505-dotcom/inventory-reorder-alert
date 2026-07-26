#!/usr/bin/env python3
"""
Inventory Reorder Alert System
A robust stock monitoring script that reads inventory data from a CSV file,
identifies items needing restocking, and generates detailed reports.

Features:
- Flexible CSV column detection
- Priority levels (Critical/Low)
- Reorder quantity suggestions
- Console, CSV, and email reports
- Logging for audit trail
- Color-coded console output
- Configurable thresholds
- Command-line arguments
"""

import csv
import os
import sys
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# Color codes for console output (Windows compatible)
class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    # Try to disable colors on Windows if not supported
    @staticmethod
    def supports_color():
        """Check if terminal supports color output"""
        try:
            import platform
            if platform.system() == 'Windows':
                # Windows 10+ supports ANSI codes
                import subprocess
                result = subprocess.run(['cmd', '/c', 'ver'], capture_output=True, text=True)
                return '10.' in result.stdout or '11.' in result.stdout
            return True
        except:
            return False

# Disable colors if not supported
if not Colors.supports_color():
    for attr in dir(Colors):
        if not attr.startswith('_') and attr != 'supports_color':
            setattr(Colors, attr, '')

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_file: str = 'inventory_alert.log'):
    """
    Configure logging for the application
    
    Args:
        log_file: Path to log file
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================================================
# MAIN INVENTORY SYSTEM CLASS
# ============================================================================

class InventoryAlertSystem:
    """Main class to handle inventory monitoring and reporting"""
    
    def __init__(self, csv_file_path: str, healthy_multiplier: float = 1.5, 
                 critical_threshold: float = 25.0):
        """
        Initialize the inventory system with a CSV file path
        
        Args:
            csv_file_path: Path to the input CSV file
            healthy_multiplier: Multiplier for target stock level (default: 1.5)
            critical_threshold: Percentage below threshold to be Critical (default: 25%)
        """
        self.csv_file_path = csv_file_path
        self.healthy_multiplier = healthy_multiplier
        self.critical_threshold = critical_threshold
        self.inventory_data = []
        self.restock_needed = []
        self.column_mapping = self._detect_column_mapping()
        
        logger.info(f"Initialized InventoryAlertSystem with file: {csv_file_path}")
        logger.info(f"Healthy multiplier: {healthy_multiplier}, Critical threshold: {critical_threshold}%")
        
    def _detect_column_mapping(self) -> Dict[str, str]:
        """
        Detect column names in the CSV file (handles variations)
        
        Returns:
            Dictionary mapping expected fields to actual column names
        """
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader)
                
                # Common variations for each field
                possible_names = {
                    'name': ['item', 'name', 'item_name', 'product', 'description', 'product_name'],
                    'quantity': ['qty', 'quantity', 'current_qty', 'stock', 'count', 'current_quantity'],
                    'threshold': ['threshold', 'reorder_threshold', 'min_stock', 'min_qty', 'reorder_level']
                }
                
                mapping = {}
                for field, variations in possible_names.items():
                    for header in headers:
                        if header.lower().strip() in variations:
                            mapping[field] = header
                            break
                    if field not in mapping:
                        logger.warning(f"Could not find '{field}' column in CSV")
                        mapping[field] = None
                        
                logger.info(f"Column mapping detected: {mapping}")
                return mapping
                
        except Exception as e:
            logger.error(f"Error reading CSV headers: {e}")
            return {'name': None, 'quantity': None, 'threshold': None}
    
    def load_data(self) -> bool:
        """
        Load and parse the CSV file into a list of dictionaries
        
        Returns:
            Boolean indicating success
        """
        try:
            # Check if file exists
            if not os.path.exists(self.csv_file_path):
                logger.error(f"File not found: {self.csv_file_path}")
                return False
                
            with open(self.csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.inventory_data = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Extract values using column mapping
                        name = row.get(self.column_mapping['name'], '').strip()
                        quantity_str = row.get(self.column_mapping['quantity'], '').strip()
                        threshold_str = row.get(self.column_mapping['threshold'], '').strip()
                        
                        # Handle missing values with defaults
                        if not name:
                            logger.warning(f"Row {row_num}: Missing item name, skipping")
                            continue
                            
                        try:
                            quantity = int(quantity_str) if quantity_str else 0
                        except ValueError:
                            logger.warning(f"Row {row_num}: Invalid quantity '{quantity_str}' for {name}, setting to 0")
                            quantity = 0
                            
                        try:
                            threshold = int(threshold_str) if threshold_str else 0
                        except ValueError:
                            logger.warning(f"Row {row_num}: Invalid threshold '{threshold_str}' for {name}, setting to 0")
                            threshold = 0
                        
                        # Store the complete row data for future reference
                        item_data = {
                            'name': name,
                            'quantity': quantity,
                            'threshold': threshold,
                            'raw_data': row,  # Keep original data for completeness
                            'status': None,
                            'priority': None,
                            'reorder_suggestion': 0
                        }
                        self.inventory_data.append(item_data)
                        logger.debug(f"Loaded item: {name} (Qty: {quantity}, Threshold: {threshold})")
                        
                    except Exception as e:
                        logger.warning(f"Row {row_num}: Error processing row: {e}")
                        continue
                        
            logger.info(f"Loaded {len(self.inventory_data)} items from CSV")
            return True
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return False
    
    def analyze_inventory(self) -> None:
        """
        Analyze inventory levels and flag items that need restocking
        Applies priority levels and calculates reorder suggestions
        """
        self.restock_needed = []
        
        for item in self.inventory_data:
            quantity = item['quantity']
            threshold = item['threshold']
            
            # Handle edge cases
            if threshold == 0:
                item['status'] = 'No Threshold Set'
                item['priority'] = 'Unknown'
                logger.warning(f"{item['name']}: No threshold set")
                continue
                
            # Calculate percentage relative to threshold
            percentage = (quantity / threshold) * 100
            
            # Determine status and priority
            if quantity == 0:
                item['status'] = 'OUT OF STOCK'
                item['priority'] = 'Critical'
                # Suggest reorder to 2x threshold for out of stock items
                item['reorder_suggestion'] = threshold * 2
                self.restock_needed.append(item)
                logger.warning(f"{item['name']}: OUT OF STOCK - Order {item['reorder_suggestion']} units")
                
            elif quantity < threshold:
                item['status'] = 'LOW STOCK'
                if percentage < self.critical_threshold:
                    item['priority'] = 'Critical'
                else:
                    item['priority'] = 'Low'
                    
                # Calculate suggested reorder quantity
                # Use configurable healthy multiplier
                target_stock = int(threshold * self.healthy_multiplier)
                item['reorder_suggestion'] = target_stock - quantity
                self.restock_needed.append(item)
                
                logger.info(f"{item['name']}: {item['priority']} - {quantity}/{threshold} units "
                           f"({percentage:.1f}%) - Order {item['reorder_suggestion']} units")
                
            else:
                item['status'] = 'In Stock'
                item['priority'] = 'OK'
                logger.debug(f"{item['name']}: Adequately stocked ({quantity}/{threshold})")
    
    def print_restock_report(self) -> None:
        """Print a clean, formatted restock report to console with colors"""
        if not self.restock_needed:
            print(f"\n{Colors.GREEN}✅ All items are adequately stocked! No restocking needed.{Colors.RESET}")
            return
            
        # Sort by priority (Critical first)
        priority_order = {'Critical': 0, 'Low': 1, 'Out of Stock': 0}
        sorted_items = sorted(
            self.restock_needed, 
            key=lambda x: priority_order.get(x['priority'], 2)
        )
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.CYAN}📋 RESTOCK NEEDED REPORT{Colors.RESET}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"\n📦 Total items needing attention: {len(sorted_items)}\n")
        
        # Header
        print(f"{'Item Name':<25} {'Current Qty':<12} {'Threshold':<10} {'Priority':<10} {'Suggested Order':<15}")
        print("-"*80)
        
        # Individual items with colors
        for item in sorted_items:
            # Color coding by priority
            if item['priority'] == 'Critical':
                color = Colors.RED
                urgency = "🔴"
            elif item['priority'] == 'Low':
                color = Colors.YELLOW
                urgency = "🟡"
            else:
                color = Colors.WHITE
                urgency = "🔵"
                
            print(f"{color}{urgency} {item['name'][:23]:<23} {item['quantity']:<12} "
                  f"{item['threshold']:<10} {item['priority']:<10} "
                  f"{item.get('reorder_suggestion', 0):<15}{Colors.RESET}")
        
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        
        # Summary statistics with colors
        critical_count = sum(1 for i in sorted_items if i['priority'] == 'Critical')
        low_count = sum(1 for i in sorted_items if i['priority'] == 'Low')
        out_of_stock_count = sum(1 for i in sorted_items if i['quantity'] == 0)
        
        print(f"\n📊 Summary:")
        print(f"  {Colors.RED}• Critical low stock: {critical_count} items{Colors.RESET}")
        print(f"  {Colors.YELLOW}• Low stock: {low_count} items{Colors.RESET}")
        print(f"  {Colors.RED}• Out of stock: {out_of_stock_count} items{Colors.RESET}")
        
        # Print reorder total
        total_reorder = sum(i.get('reorder_suggestion', 0) for i in sorted_items)
        print(f"  {Colors.CYAN}• Total units to reorder: {total_reorder}{Colors.RESET}")
        
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    def export_csv_report(self, output_file: Optional[str] = None) -> None:
        """
        Export the restock report to a CSV file with date in filename
        
        Args:
            output_file: Name of the output CSV file (auto-generates if None)
        """
        if not self.restock_needed:
            print("ℹ️  No items to export to CSV")
            logger.info("No items to export to CSV")
            return
            
        # Auto-generate filename with date if not provided
        if output_file is None:
            date_str = datetime.now().strftime("%Y%m%d")
            output_file = f'restock_report_{date_str}.csv'
            
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['Item Name', 'Current Quantity', 'Threshold', 
                            'Status', 'Priority', 'Suggested Reorder Quantity']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                writer.writeheader()
                for item in self.restock_needed:
                    writer.writerow({
                        'Item Name': item['name'],
                        'Current Quantity': item['quantity'],
                        'Threshold': item['threshold'],
                        'Status': item['status'],
                        'Priority': item['priority'],
                        'Suggested Reorder Quantity': item.get('reorder_suggestion', 0)
                    })
            
            print(f"{Colors.GREEN}✅ Restock report exported to: {output_file}{Colors.RESET}")
            logger.info(f"Exported restock report to {output_file}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error exporting CSV report: {e}{Colors.RESET}")
            logger.error(f"Error exporting CSV report: {e}")
    
    def generate_email_alert(self) -> str:
        """
        Generate a formatted email alert mimicking a real restock notification
        
        Returns:
            Formatted email string
        """
        if not self.restock_needed:
            return "Subject: Restock Alert - All Items Adequately Stocked\n\n" \
                   "All inventory items are currently at acceptable levels."
        
        sorted_items = sorted(
            self.restock_needed,
            key=lambda x: 0 if x['priority'] == 'Critical' else 1
        )
        
        subject = f"⚠️ URGENT: {len(self.restock_needed)} Items Need Restocking"
        
        body = f"""
Good Morning Warehouse Team,

This automated inventory check ({datetime.now().strftime('%Y-%m-%d %H:%M')}) has identified 
{len(self.restock_needed)} items that require immediate attention.

CRITICAL ITEMS (Immediate Action Required):
"""
        critical_items = [i for i in sorted_items if i['priority'] == 'Critical']
        low_items = [i for i in sorted_items if i['priority'] == 'Low']
        
        if critical_items:
            for item in critical_items:
                body += f"  • {item['name']}: {item['quantity']} units (Threshold: {item['threshold']}) "
                body += f"- Suggest reordering {item.get('reorder_suggestion', 0)} units\n"
        else:
            body += "  None\n"
            
        body += "\nLOW STOCK ITEMS (Plan for Restocking):\n"
        if low_items:
            for item in low_items:
                body += f"  • {item['name']}: {item['quantity']} units (Threshold: {item['threshold']}) "
                body += f"- Suggest reordering {item.get('reorder_suggestion', 0)} units\n"
        else:
            body += "  None\n"
            
        body += f"\nPlease review the attached CSV report for complete details.\n"
        body += f"\nThis is an automated message from the Inventory Alert System.\n"
        body += f"Contact IT support if you need assistance with this system."
        
        full_email = f"Subject: {subject}\n\n{body}"
        logger.info(f"Generated email alert for {len(self.restock_needed)} items")
        return full_email
    
    def print_email_alert(self) -> None:
        """Print the formatted email alert to console"""
        email_content = self.generate_email_alert()
        print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.MAGENTA}📧 SIMULATED EMAIL ALERT{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(email_content)
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Execute the complete inventory analysis workflow
        
        Returns:
            Dictionary with analysis results
        """
        print(f"\n{Colors.CYAN}🚀 Starting Inventory Analysis...{Colors.RESET}")
        print("-"*80)
        
        if not self.load_data():
            return {'success': False, 'message': 'Failed to load data'}
        
        self.analyze_inventory()
        
        # Generate reports
        self.print_restock_report()
        self.export_csv_report()
        self.print_email_alert()
        
        # Reflection note
        print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"{Colors.BLUE}💡 REFLECTION NOTE: What Would I Improve?{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        print(f"""
{Colors.CYAN}With more time, I would enhance this system with:{Colors.RESET}

1. {Colors.BOLD}Automated Scheduling{Colors.RESET}: Implement a cron job or use APScheduler to run this
   script daily at 8:00 AM, sending alerts directly to stakeholders' inboxes.

2. {Colors.BOLD}Supplier Integration{Colors.RESET}: Connect with supplier APIs to automatically place
   orders when stock hits critical levels, reducing manual intervention.

3. {Colors.BOLD}Historical Trend Tracking{Colors.RESET}: Store daily snapshots to identify patterns - 
   predicting when items will hit thresholds before they actually do, enabling
   proactive restocking rather than reactive.

4. {Colors.BOLD}Multi-Warehouse Support{Colors.RESET}: Handle multiple locations with different 
   thresholds and lead times, optimizing distribution across the supply chain.

5. {Colors.BOLD}Web Dashboard{Colors.RESET}: Create a real-time web interface for management
   to monitor stock levels, trends, and receive alerts visually.
        """)
        print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
        
        result = {
            'success': True,
            'total_items': len(self.inventory_data),
            'items_needing_restock': len(self.restock_needed),
            'critical_items': sum(1 for i in self.restock_needed if i['priority'] == 'Critical'),
            'total_reorder_units': sum(i.get('reorder_suggestion', 0) for i in self.restock_needed)
        }
        
        logger.info(f"Analysis complete: {result}")
        return result


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_sample_csv(filename: str = 'stock_data.csv') -> None:
    """
    Create a sample CSV file for testing purposes
    
    Args:
        filename: Name of the CSV file to create
    """
    sample_data = [
        ['Item', 'Quantity', 'Threshold'],
        ['Widget A', '150', '50'],
        ['Gadget B', '12', '20'],
        ['Tool C', '5', '25'],
        ['Part D', '0', '15'],
        ['Material E', '80', '100'],
        ['Component F', '3', '10'],
        ['Product G', '45', '50'],
        ['Accessory H', '200', '100'],
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(sample_data)
    
    print(f"{Colors.GREEN}📝 Created sample CSV file: {filename}{Colors.RESET}")
    logger.info(f"Created sample CSV file: {filename}")


def parse_arguments():
    """
    Parse command-line arguments
    
    Returns:
        Parsed arguments object
    """
    parser = argparse.ArgumentParser(
        description='Inventory Reorder Alert System - Monitor stock levels and generate restock reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python inventory_alert.py
  python inventory_alert.py my_inventory.csv
  python inventory_alert.py stock.csv --export report.csv --threshold 1.8 --critical 20
  python inventory_alert.py stock.csv --log-file inventory.log
        """
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        default='stock_data.csv',
        help='Path to the inventory CSV file (default: stock_data.csv)'
    )
    
    parser.add_argument(
        '--export', '-e',
        default=None,
        help='Output CSV report filename (default: restock_report_YYYYMMDD.csv)'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=1.5,
        help='Healthy stock multiplier (default: 1.5)'
    )
    
    parser.add_argument(
        '--critical', '-c',
        type=float,
        default=25.0,
        help='Critical threshold percentage (default: 25%%)'
    )
    
    parser.add_argument(
        '--log-file', '-l',
        default='inventory_alert.log',
        help='Log file path (default: inventory_alert.log)'
    )
    
    parser.add_argument(
        '--no-color', 
        action='store_true',
        help='Disable colored console output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress console output (log only to file)'
    )
    
    return parser.parse_args()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_') and attr != 'supports_color':
                setattr(Colors, attr, '')
    
    # Reconfigure logging if specified
    if args.log_file:
        global logger
        logger = setup_logging(args.log_file)
    
    # Quiet mode - suppress stdout
    if args.quiet:
        sys.stdout = open(os.devnull, 'w')
    
    print(f"{Colors.CYAN}🏭 Inventory Reorder Alert System v2.0{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
    
    csv_file = args.file
    
    # Create sample data if file doesn't exist
    if not os.path.exists(csv_file):
        print(f"{Colors.YELLOW}ℹ️  Stock file not found. Creating sample data...{Colors.RESET}")
        create_sample_csv(csv_file)
    
    # Create and run the inventory system
    system = InventoryAlertSystem(
        csv_file_path=csv_file,
        healthy_multiplier=args.threshold,
        critical_threshold=args.critical
    )
    
    results = system.run_full_analysis()
    
    # Restore stdout if quiet mode was enabled
    if args.quiet:
        sys.stdout = sys.__stdout__
    
    if results['success']:
        print(f"\n{Colors.GREEN}✅ Analysis complete!{Colors.RESET}")
        print(f"   Processed: {results['total_items']} items")
        print(f"   Needs attention: {results['items_needing_restock']} items")
        print(f"   Critical: {results['critical_items']} items")
        print(f"   Total units to reorder: {results['total_reorder_units']}")
    else:
        print(f"\n{Colors.RED}❌ Analysis failed: {results.get('message', 'Unknown error')}{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}🏁 Program finished.{Colors.RESET}")
    logger.info("Program finished successfully")


if __name__ == "__main__":
    main()