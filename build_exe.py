import os
import subprocess
import sys
import shutil

def main():
    print("========================================")
    print("Bid Information Scraper - EXE Builder")
    print("========================================")
    print()
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Create dist directory if it doesn't exist
    if not os.path.exists("dist"):
        os.makedirs("dist")
    
    # Build the scraper executable
    print("Building scraper executable with PyInstaller...")
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--name=BidScraper",
        "--onefile",  # Create a single executable
        "--clean",    # Clean PyInstaller cache
        "--add-data", "config.ini;.",  # Add config file
        "--icon=NONE",  # No icon (replace with icon path if you have one)
        "scraper.py"    # Main script
    ], check=True)
    
    # Build the scheduler executable
    print("\nBuilding scheduler executable with PyInstaller...")
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--name=BidScheduler",
        "--onefile",  # Create a single executable
        "--clean",    # Clean PyInstaller cache
        "--add-data", "config.ini;.",  # Add config file
        "--icon=NONE",  # No icon (replace with icon path if you have one)
        "scheduler.py"   # Scheduler script
    ], check=True)
    
    # Copy additional files to the dist directory
    print("Copying additional files...")
    shutil.copy("README.md", os.path.join("dist", "README.md"))
    shutil.copy("config.ini", os.path.join("dist", "config.ini"))
    shutil.copy("VERSION.md", os.path.join("dist", "VERSION.md"))
    
    # Create a simple batch file to run the scraper
    with open(os.path.join("dist", "start_scraper.bat"), "w") as f:
        f.write('@echo off\r\n')
        f.write('echo Starting Bid Scraper...\r\n')
        f.write('BidScraper.exe\r\n')
        f.write('pause\r\n')
    
    # Create a simple batch file to run the scheduler
    with open(os.path.join("dist", "start_scheduler.bat"), "w") as f:
        f.write('@echo off\r\n')
        f.write('echo Starting Bid Scheduler...\r\n')
        f.write('echo This will run in the background. Close this window to stop.\r\n')
        f.write('BidScheduler.exe\r\n')
        f.write('pause\r\n')
    
    print()
    print("========================================")
    print("Build completed!")
    print("Executable files created in the 'dist' folder")
    print("========================================")
    print()
    print("Usage:")
    print("1. Navigate to the 'dist' folder")
    print("2. Run one of the following:")
    print("   - BidScraper.exe (or start_scraper.bat) - for manual scraping")
    print("   - BidScheduler.exe (or start_scheduler.bat) - for scheduled scraping")
    print()

if __name__ == "__main__":
    main()