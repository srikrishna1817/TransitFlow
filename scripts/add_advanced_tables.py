import mysql.connector
import sys
sys.path.append('..')
from config.db_config import DB_CONFIG

def create_advanced_tables():
    """Create new tables for Phase 2B"""
    
    print("=" * 60)
    print("CREATING ADVANCED SCHEDULING TABLES")
    print("=" * 60)
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Check what tables exist to avoid duplicating
    tables = [
        """
        CREATE TABLE IF NOT EXISTS crew_roster (
            crew_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(100),
            crew_type VARCHAR(20),  
            experience_years INT,
            route_certifications JSON,  
            max_hours_per_day INT DEFAULT 8,
            current_status VARCHAR(20) DEFAULT 'Available',  
            last_duty_date DATE,
            total_hours_this_week DECIMAL(5,2) DEFAULT 0.0,
            home_depot VARCHAR(50),  
            language_skills JSON,  
            date_of_joining DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS crew_assignments (
            assignment_id INT AUTO_INCREMENT PRIMARY KEY,
            schedule_date DATE NOT NULL,
            train_id VARCHAR(20) NOT NULL,
            route VARCHAR(50) NOT NULL,  
            shift_start TIME NOT NULL,
            shift_end TIME NOT NULL,
            driver_id VARCHAR(20),
            conductor_id VARCHAR(20),
            relief_driver_id VARCHAR(20),
            relief_conductor_id VARCHAR(20),
            total_hours DECIMAL(5,2),
            home_depot VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS scenarios_log (
            scenario_id INT AUTO_INCREMENT PRIMARY KEY,
            scenario_type VARCHAR(50) NOT NULL,  
            scenario_date DATE NOT NULL,
            parameters JSON,  
            impact_analysis JSON,  
            recommendations JSON,  
            created_by VARCHAR(50) DEFAULT 'System',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS hmrl_routes (
            route_id INT AUTO_INCREMENT PRIMARY KEY,
            route_name VARCHAR(50) NOT NULL UNIQUE,  
            route_code VARCHAR(10),  
            start_station VARCHAR(100),
            end_station VARCHAR(100),
            total_distance_km DECIMAL(5,2),
            total_stations INT,
            operating_hours_start TIME,
            operating_hours_end TIME,
            peak_headway_minutes INT,
            offpeak_headway_minutes INT,
            estimated_trains_required INT,
            depot_location VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    
    # Try inserting the default routes safely
    insert_routes = """
    INSERT IGNORE INTO hmrl_routes (route_name, route_code, start_station, end_station, total_distance_km, total_stations, operating_hours_start, operating_hours_end, peak_headway_minutes, offpeak_headway_minutes, estimated_trains_required, depot_location) VALUES
    ('Red Line', 'R1', 'Miyapur', 'LB Nagar', 29.87, 27, '06:00:00', '23:00:00', 3, 6, 25, 'Miyapur'),
    ('Green Line', 'G2', 'JBS Parade Ground', 'MGBS', 9.6, 9, '06:00:00', '23:00:00', 5, 8, 12, 'Secunderabad'),
    ('Blue Line', 'B3', 'Nagole', 'Raidurg', 28.0, 23, '06:00:00', '23:00:00', 3, 6, 23, 'Uppal');
    """
    
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
            print("✓ Table created successfully or already exists.")
        except Exception as e:
            print(f"✗ Error: {e}")
            
    try:
        cursor.execute(insert_routes)
        print("✓ Route definition defaults injected.")
    except Exception as e:
        print(f"✗ Route insertion Error: {e}")
        
    # Helper indices skipping creation checks for brevity in simple setups
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("ADVANCED TABLES READY!")
    print("=" * 60)

if __name__ == "__main__":
    create_advanced_tables()
