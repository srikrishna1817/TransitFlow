import pandas as pd
import random
import sys
import json
sys.path.append('..')
from utils.db_utils import db
from datetime import datetime, timedelta

def generate_hmrl_crew():
    """Generate realistic HMRL crew roster"""
    
    print("Generating HMRL crew roster...")
    
    # Indian names
    first_names = ["Rajesh", "Priya", "Amit", "Sneha", "Vijay", "Lakshmi", "Kiran", "Divya", "Sanjay", "Kavita", 
                   "Ramesh", "Swati", "Suresh", "Anita", "Mahesh", "Deepa", "Ganesh", "Radha", "Praveen", "Sunita",
                   "Krishna", "Padma", "Ravi", "Sudha", "Anil", "Jyoti", "Venkat", "Manjula", "Prakash", "Sarita"]
    last_names = ["Kumar", "Reddy", "Rao", "Sharma", "Singh", "Patel", "Nair", "Das", "Gupta", "Prasad",
                  "Srinivas", "Murthy", "Chowdary", "Naidu", "Varma", "Menon", "Iyer", "Joshi", "Desai", "Pillai"]
    
    crew_data = []
    crew_id_counter = {'Driver': 1, 'Conductor': 1, 'Relief_Driver': 1, 'Relief_Conductor': 1}
    
    # Generate 120 crew members
    # 55 Drivers, 40 Conductors, 15 Relief Drivers, 10 Relief Conductors
    crew_distribution = [
        ('Driver', 55),
        ('Conductor', 40),
        ('Relief_Driver', 15),
        ('Relief_Conductor', 10)
    ]
    
    for crew_type, count in crew_distribution:
        for _ in range(count):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            experience = random.randint(1, 15)
            
            # Route certifications based on experience
            if experience >= 5:
                certifications = ["Red Line", "Blue Line", "Green Line"]  # Senior, all routes
            elif experience >= 2:
                certifications = random.sample(["Red Line", "Blue Line", "Green Line"], 2)  # Mid-level, 2 routes
            else:
                certifications = [random.choice(["Green Line", "Blue Line"])]  # New, 1 route (not Red Line initially)
            
            # Language skills
            languages = ["Telugu", "Hindi"]
            if random.random() > 0.6:  # 40% speak English
                languages.append("English")
            
            # Home depot
            depot = random.choice(["Miyapur", "Uppal", "Secunderabad"])
            
            # Status
            status_prob = random.random()
            if status_prob < 0.85:
                status = "Available"
            elif status_prob < 0.92:
                status = "On_Leave"
            else:
                status = "Sick"
            
            # Recent duty
            last_duty = datetime.now().date() - timedelta(days=random.randint(0, 7))
            hours_this_week = random.uniform(0, 40) if status == "Available" else 0
            
            # Date of joining
            doj = datetime.now().date() - timedelta(days=experience * 365 + random.randint(0, 365))
            
            prefix = 'DRV' if 'Driver' in crew_type else 'CON'
            crew_id = f"{prefix}_{crew_id_counter[crew_type]:03d}"
            crew_id_counter[crew_type] += 1
            
            crew_data.append({
                'crew_id': crew_id,
                'name': name,
                'crew_type': crew_type,
                'experience_years': experience,
                'route_certifications': json.dumps(certifications),  # JSON in MySQL
                'max_hours_per_day': 8,
                'current_status': status,
                'last_duty_date': last_duty,
                'total_hours_this_week': round(hours_this_week, 2),
                'home_depot': depot,
                'language_skills': json.dumps(languages),
                'date_of_joining': doj
            })
    
    # Create DataFrame
    crew_df = pd.DataFrame(crew_data)
    
    # Insert into database
    success = db.insert_dataframe(crew_df, 'crew_roster', if_exists='replace')
    
    if success:
        print(f"✓ Generated and inserted {len(crew_df)} crew members")
        print(f"  - Drivers: {len(crew_df[crew_df['crew_type']=='Driver'])}")
        print(f"  - Conductors: {len(crew_df[crew_df['crew_type']=='Conductor'])}")
        print(f"  - Relief Drivers: {len(crew_df[crew_df['crew_type']=='Relief_Driver'])}")
        print(f"  - Relief Conductors: {len(crew_df[crew_df['crew_type']=='Relief_Conductor'])}")
    else:
        print("✗ Failed to insert crew data")

if __name__ == "__main__":
    generate_hmrl_crew()
