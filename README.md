# 📦 Inventory Reorder Alert System

> An automated inventory monitoring system that reads stock data from CSV files, identifies items needing restocking, and generates comprehensive reports with priority levels and reorder suggestions.

## 🎯 Key Features

- 📄 **CSV File Handling** - Reads inventory data with flexible column mapping
- 🧠 **Smart Analysis** - Compares current stock against thresholds with priority classification
- 🔀 **Priority Levels** - Critical (<25%) vs Low (25-100%) classification
- 📧 **Email Simulation** - Professional restock alert format with subject and body
- 📊 **Multiple Reports** - Console, CSV (date-stamped), and email formats
- 🤖 **Automation Ready** - Command-line arguments, logging, and scheduling support
- 🎨 **Color Output** - Visual indicators for easy scanning (RED = Critical, YELLOW = Low)
- 📝 **Audit Logging** - Complete log file with timestamps for all actions

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Gani505-dotcom/inventory-reorder-alert.git
cd inventory-reorder-alert

# No dependencies required - uses Python standard library only!
Basic Usage
bash
# Run with default sample data (auto-creates stock_data.csv)
python inventory_alert.py

# Run with your own inventory file
python inventory_alert.py my_inventory.csv
Sample Output
text
================================================================================
📋 RESTOCK NEEDED REPORT
Generated: 2026-07-26 14:36:41
================================================================================

📦 Total items needing attention: 6

Item Name                 Current Qty  Threshold  Priority   Suggested Order
--------------------------------------------------------------------------------
🔴 Tool C                  5            25         Critical   32             
🔴 Part D                  0            15         Critical   30             
🟡 Gadget B                12           20         Low        18             
🟡 Material E              80           100        Low        70             
================================================================================

📊 Summary:
  • Critical low stock: 2 items
  • Low stock: 4 items
  • Out of stock: 1 items
  • Total units to reorder: 192
================================================================================
📋 CSV Format
Your CSV file should contain these columns (headers are flexible):

Column	Description	Examples
Item	Product/Item name	Coffee Beans, Widget A
Quantity	Current stock level	150, 12, 0
Threshold	Minimum stock before reorder	50, 20, 15
Sample CSV
csv
Item,Quantity,Threshold
Widget A,150,50
Gadget B,12,20
Tool C,5,25
Part D,0,15
Supported Column Name Variations
Standard Field	Recognized Variations
Item	item, name, item_name, product, description, product_name
Quantity	qty, quantity, current_qty, stock, count, current_quantity
Threshold	threshold, reorder_threshold, min_stock, min_qty, reorder_level

🎮 Command-Line Options
Argument	Description	Default
file	Path to inventory CSV file	stock_data.csv
--export, -e	Output CSV filename	restock_report_YYYYMMDD.csv
--threshold, -t	Healthy stock multiplier	1.5
--critical, -c	Critical threshold percentage	25.0
--log-file, -l	Log file path	inventory_alert.log
--no-color	Disable colored console output	False
--quiet, -q	Suppress console output (log only)	False

Usage Examples
bash
# Basic usage with custom file
python inventory_alert.py cafe_inventory.csv

# Custom thresholds (more conservative)
python inventory_alert.py stock.csv --threshold 2.0 --critical 30

# Export with custom filename
python inventory_alert.py inventory.csv --export weekly_report.csv

# Full featured with all options
python inventory_alert.py inventory.csv --export report.csv --threshold 1.8 --critical 20 --log-file system.log

# Quiet mode (log only to file)
python inventory_alert.py stock.csv --quiet --log-file daily_check.log

# Disable colors for non-ANSI terminals
python inventory_alert.py stock.csv --no-color

📁 Generated Files
File	Description
restock_report_YYYYMMDD.csv	Dated CSV report with flagged items
stock_data.csv	Auto-generated sample data (if not provided)

🏗️ Project Structure
text
inventory-reorder-alert/
├── inventory_alert.py          # Main application script
├── README.md                   # This file
├── stock_data.csv              # Sample inventory data (auto-created)
├── restock_report_20260726.csv # Generated reports

🔧 Advanced Features
Priority Classification
Priority	Condition	Action
CRITICAL	Quantity < 25% of threshold	Immediate action required
LOW	25% ≤ Quantity < 100% of threshold	Plan for restocking
OUT OF STOCK	Quantity = 0	Emergency restocking
OK	Quantity ≥ Threshold	Adequately stocked
Reorder Calculation
The system suggests reordering based on a healthy multiplier (default: 1.5):

text
Suggested Order = (Threshold × Healthy Multiplier) - Current Quantity

Example: Tool C
Current: 5 units
Threshold: 25 units
Healthy Stock = 25 × 1.5 = 37.5 → 38 units
Suggested Order = 38 - 5 = 33 units
Email Alert Format
The system generates professional email alerts:

text
Subject: ⚠️ URGENT: 6 Items Need Restocking

Good Morning Warehouse Team,

This automated inventory check (2026-07-26 14:36) has identified 
6 items that require immediate attention.

CRITICAL ITEMS (Immediate Action Required):
  • Tool C: 5 units (Threshold: 25) - Suggest reordering 32 units
  • Part D: 0 units (Threshold: 15) - Suggest reordering 30 units

LOW STOCK ITEMS (Plan for Restocking):
  • Gadget B: 12 units (Threshold: 20) - Suggest reordering 18 units
🧪 Edge Cases Handled
✅ Missing CSV file → Auto-generates sample data
✅ Missing columns → Flexible column name matching
✅ Empty values → Defaults to 0
✅ Invalid numbers → Handles gracefully with warnings
✅ Zero threshold → Marked as "No Threshold Set"
✅ Out of stock → CRITICAL priority with 2x threshold reorder
✅ Negative quantities → Converted to 0
✅ Duplicate items → Processed individually

📊 Example Use Cases
Retail Store
bash
python inventory_alert.py store_inventory.csv --threshold 1.8 --critical 20
Restaurant/Cafe
bash
python inventory_alert.py cafe_supplies.csv --export daily_restock.csv
Manufacturing
bash
python inventory_alert.py parts_inventory.csv --log-file factory.log
🔄 Automation Setup
Windows Task Scheduler
Open Task Scheduler

Create Basic Task

Trigger: Daily at 8:00 AM

Action: python "C:\path\to\inventory_alert.py" stock.csv --quiet

Linux Cron Job
bash
# Run daily at 8:00 AM
0 8 * * * cd /path/to/inventory && python3 inventory_alert.py stock.csv --quiet >> /var/log/inventory.log 2>&1
Docker Deployment
dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY inventory_alert.py .
CMD ["python", "inventory_alert.py", "stock.csv"]
🤝 Contributing
Contributions are welcome! Here's how you can help:

Fork the repository

Create a feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request


🙏 Acknowledgments
Built with Python standard library - no external dependencies!

Inspired by real-world warehouse inventory management needs

Designed for easy integration with existing workflows

📞 Support
For issues and feature requests, please open an issue.

🏆 Bonus Features
Feature	Status
Simulated Email Alert	✅
Priority Levels (Critical/Low)	✅
Reorder Quantity Suggestions	✅
CSV Export with Date Stamping	✅
Reflection Note	✅
Logging System	✅
Color-Coded Output	✅
Command-Line Arguments	✅
Flexible Column Mapping	✅
