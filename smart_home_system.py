"""
Smart Home Lighting Automation System
Using Occupancy Detection and Intelligent Energy Management
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 7)
plt.rcParams['font.size'] = 10

class OccupancySensor:
    """Simulates occupancy detection using motion sensors and light sensors"""
    
    def __init__(self, room_name, sensor_sensitivity=0.75):
        self.room_name = room_name
        self.sensor_sensitivity = sensor_sensitivity
        self.occupancy_history = []
        self.motion_detected = False
        self.light_level = 0
        
    def detect_occupancy(self, motion_signal, ambient_light):
        """
        Detect occupancy based on motion and ambient light levels
        motion_signal: 0-1 (probability of motion)
        ambient_light: 0-100 (lux level)
        """
        # Occupancy is detected if motion exceeds sensitivity threshold
        # or if light level is low and motion is detected
        occupancy = False
        
        if motion_signal > self.sensor_sensitivity:
            occupancy = True
        elif motion_signal > (self.sensor_sensitivity * 0.5) and ambient_light < 50:
            occupancy = True
            
        self.motion_detected = occupancy
        self.light_level = ambient_light
        self.occupancy_history.append({
            'timestamp': datetime.now(),
            'occupancy': occupancy,
            'motion_signal': motion_signal,
            'ambient_light': ambient_light
        })
        
        return occupancy


class SmartLightingController:
    """Controls lighting based on occupancy and energy optimization"""
    
    def __init__(self, room_name, light_power_watts=60, min_brightness=10, max_brightness=100):
        self.room_name = room_name
        self.light_power_watts = light_power_watts
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.brightness_level = 0
        self.is_on = False
        self.control_history = []
        self.energy_consumed = 0  # in Wh
        
    def control_light(self, occupancy, ambient_light, time_of_day, user_preference=None):
        """
        Control light based on occupancy and ambient light
        time_of_day: hour (0-23)
        user_preference: dict with 'brightness' and 'mode' keys
        """
        if occupancy:
            # Calculate brightness based on ambient light
            if ambient_light < 30:
                target_brightness = self.max_brightness
            elif ambient_light < 100:
                target_brightness = max(self.min_brightness, self.max_brightness - (ambient_light / 100) * 50)
            else:
                target_brightness = self.min_brightness
                
            # Apply user preference if available
            if user_preference and 'brightness' in user_preference:
                target_brightness = user_preference['brightness']
                
            # Time-based adjustment (dimmer in evening)
            if 20 <= time_of_day <= 23 or 0 <= time_of_day < 6:
                target_brightness = max(self.min_brightness, target_brightness * 0.7)
                
            self.brightness_level = target_brightness
            self.is_on = True
        else:
            # Turn off light when room is unoccupied
            self.brightness_level = 0
            self.is_on = False
            
        # Record control action
        self.control_history.append({
            'timestamp': datetime.now(),
            'is_on': self.is_on,
            'brightness': self.brightness_level,
            'occupancy': occupancy,
            'ambient_light': ambient_light
        })
        
        return self.is_on, self.brightness_level
    
    def calculate_energy_consumption(self, duration_hours):
        """Calculate energy consumption for a given duration"""
        # Energy = Power * Time * (Brightness/100)
        if self.is_on:
            energy = (self.light_power_watts / 1000) * duration_hours * (self.brightness_level / 100)
        else:
            energy = 0
        self.energy_consumed += energy
        return energy


class SmartHomeSystem:
    """Main system integrating multiple rooms and sensors"""
    
    def __init__(self):
        self.rooms = {}
        self.sensors = {}
        self.controllers = {}
        self.daily_energy_log = []
        self.system_events = []
        
    def add_room(self, room_name, light_power_watts=60):
        """Add a room to the smart home system"""
        self.rooms[room_name] = {
            'name': room_name,
            'light_power': light_power_watts,
            'created_at': datetime.now()
        }
        self.sensors[room_name] = OccupancySensor(room_name)
        self.controllers[room_name] = SmartLightingController(room_name, light_power_watts)
        
    def simulate_day(self, date=None, num_intervals=288):
        """
        Simulate a full day with 5-minute intervals (288 intervals in 24 hours)
        """
        if date is None:
            date = datetime.now().date()
            
        daily_data = []
        total_energy = 0
        
        for interval in range(num_intervals):
            hour = (interval * 5) / 60  # Convert interval to hours
            time_of_day = int(hour)
            
            for room_name in self.rooms:
                # Simulate occupancy patterns
                motion_signal = self._generate_occupancy_pattern(time_of_day, interval)
                ambient_light = self._generate_light_pattern(time_of_day)
                
                # Detect occupancy
                occupancy = self.sensors[room_name].detect_occupancy(motion_signal, ambient_light)
                
                # Control light
                is_on, brightness = self.controllers[room_name].control_light(
                    occupancy, ambient_light, time_of_day
                )
                
                # Calculate energy for this interval (5 minutes = 1/12 hour)
                energy = self.controllers[room_name].calculate_energy_consumption(5/60)
                total_energy += energy
                
                daily_data.append({
                    'date': date,
                    'time': f"{time_of_day:02d}:{(interval % 12) * 5:02d}",
                    'hour': time_of_day,
                    'room': room_name,
                    'occupancy': occupancy,
                    'ambient_light': ambient_light,
                    'light_on': is_on,
                    'brightness': brightness,
                    'energy_consumed_wh': energy,
                    'motion_signal': motion_signal
                })
        
        self.daily_energy_log.append({
            'date': date,
            'total_energy_kwh': total_energy / 1000,
            'num_rooms': len(self.rooms)
        })
        
        return pd.DataFrame(daily_data)
    
    def _generate_occupancy_pattern(self, hour, interval):
        """Generate realistic occupancy patterns for different times of day"""
        # Morning: 6-9 AM (high occupancy)
        if 6 <= hour < 9:
            base_signal = 0.8 + np.random.normal(0, 0.1)
        # Work hours: 9 AM - 5 PM (low occupancy in home)
        elif 9 <= hour < 17:
            base_signal = 0.2 + np.random.normal(0, 0.1)
        # Evening: 5 PM - 11 PM (high occupancy)
        elif 17 <= hour < 23:
            base_signal = 0.75 + np.random.normal(0, 0.1)
        # Night: 11 PM - 6 AM (low occupancy)
        else:
            base_signal = 0.1 + np.random.normal(0, 0.05)
        
        return np.clip(base_signal, 0, 1)
    
    def _generate_light_pattern(self, hour):
        """Generate realistic ambient light patterns"""
        # Sunrise around 6 AM, sunset around 6 PM
        if 6 <= hour < 12:
            # Morning: increasing light
            light = 20 + (hour - 6) * 15
        elif 12 <= hour < 18:
            # Afternoon: peak light
            light = 100 - (hour - 12) * 5
        elif 18 <= hour < 20:
            # Evening: decreasing light
            light = 70 - (hour - 18) * 35
        else:
            # Night: minimal light
            light = 5
        
        return np.clip(light + np.random.normal(0, 5), 0, 100)
    
    def get_system_report(self):
        """Generate comprehensive system report"""
        report = {
            'total_rooms': len(self.rooms),
            'rooms': list(self.rooms.keys()),
            'total_energy_kwh': sum([log['total_energy_kwh'] for log in self.daily_energy_log]),
            'average_daily_energy_kwh': np.mean([log['total_energy_kwh'] for log in self.daily_energy_log]) if self.daily_energy_log else 0,
            'simulation_days': len(self.daily_energy_log)
        }
        return report


def generate_visualizations(system, daily_data):
    """Generate comprehensive visualizations for the report"""
    
    # 1. Daily Energy Consumption by Room
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Smart Home Lighting System - Energy Analysis', fontsize=16, fontweight='bold')
    
    # Energy consumption by room
    room_energy = daily_data.groupby('room')['energy_consumed_wh'].sum()
    axes[0, 0].bar(room_energy.index, room_energy.values, color='steelblue', edgecolor='black')
    axes[0, 0].set_title('Total Energy Consumption by Room', fontweight='bold')
    axes[0, 0].set_ylabel('Energy (Wh)')
    axes[0, 0].set_xlabel('Room')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Occupancy pattern throughout the day
    occupancy_by_hour = daily_data.groupby('hour')['occupancy'].mean() * 100
    axes[0, 1].plot(occupancy_by_hour.index, occupancy_by_hour.values, marker='o', 
                    linewidth=2, markersize=6, color='green')
    axes[0, 1].fill_between(occupancy_by_hour.index, occupancy_by_hour.values, alpha=0.3, color='green')
    axes[0, 1].set_title('Occupancy Pattern Throughout the Day', fontweight='bold')
    axes[0, 1].set_ylabel('Occupancy (%)')
    axes[0, 1].set_xlabel('Hour of Day')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Light brightness by hour
    brightness_by_hour = daily_data[daily_data['light_on']].groupby('hour')['brightness'].mean()
    axes[1, 0].bar(brightness_by_hour.index, brightness_by_hour.values, color='orange', edgecolor='black')
    axes[1, 0].set_title('Average Light Brightness When On', fontweight='bold')
    axes[1, 0].set_ylabel('Brightness Level (%)')
    axes[1, 0].set_xlabel('Hour of Day')
    axes[1, 0].set_ylim([0, 100])
    
    # Energy consumption by hour
    energy_by_hour = daily_data.groupby('hour')['energy_consumed_wh'].sum()
    axes[1, 1].bar(energy_by_hour.index, energy_by_hour.values, color='red', edgecolor='black', alpha=0.7)
    axes[1, 1].set_title('Energy Consumption by Hour', fontweight='bold')
    axes[1, 1].set_ylabel('Energy (Wh)')
    axes[1, 1].set_xlabel('Hour of Day')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/report_project/fig_energy_analysis.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_energy_analysis.png")
    plt.close()
    
    # 2. Occupancy vs Light Control
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Create hourly summary
    hourly_summary = daily_data.groupby('hour').agg({
        'occupancy': 'mean',
        'light_on': 'mean',
        'ambient_light': 'mean'
    }) * 100
    
    x = hourly_summary.index
    width = 0.25
    
    ax.bar(x - width, hourly_summary['occupancy'], width, label='Occupancy', color='steelblue', edgecolor='black')
    ax.bar(x, hourly_summary['light_on'], width, label='Light On', color='orange', edgecolor='black')
    ax.bar(x + width, hourly_summary['ambient_light'], width, label='Ambient Light', color='green', edgecolor='black')
    
    ax.set_xlabel('Hour of Day', fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontweight='bold')
    ax.set_title('Occupancy Detection vs Light Control vs Ambient Light', fontweight='bold', fontsize=14)
    ax.legend(loc='upper left', fontsize=10)
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/report_project/fig_occupancy_control.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_occupancy_control.png")
    plt.close()
    
    # 3. System Performance Metrics
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('System Performance Metrics', fontsize=14, fontweight='bold')
    
    # Light efficiency (brightness when occupancy is high)
    high_occupancy = daily_data[daily_data['occupancy'] == True]
    efficiency_by_hour = high_occupancy.groupby('hour')['brightness'].mean()
    
    axes[0].plot(efficiency_by_hour.index, efficiency_by_hour.values, marker='s', 
                 linewidth=2.5, markersize=7, color='purple')
    axes[0].fill_between(efficiency_by_hour.index, efficiency_by_hour.values, alpha=0.2, color='purple')
    axes[0].set_title('Light Brightness During Occupancy', fontweight='bold')
    axes[0].set_ylabel('Brightness Level (%)')
    axes[0].set_xlabel('Hour of Day')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_ylim([0, 100])
    
    # Motion signal strength
    motion_by_hour = daily_data.groupby('hour')['motion_signal'].mean()
    axes[1].bar(motion_by_hour.index, motion_by_hour.values, color='teal', edgecolor='black', alpha=0.7)
    axes[1].set_title('Average Motion Signal Strength', fontweight='bold')
    axes[1].set_ylabel('Motion Signal (0-1)')
    axes[1].set_xlabel('Hour of Day')
    axes[1].set_ylim([0, 1])
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/report_project/fig_performance_metrics.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_performance_metrics.png")
    plt.close()
    
    # 4. Multi-day energy trend
    fig, ax = plt.subplots(figsize=(12, 6))
    
    daily_energy = pd.DataFrame(system.daily_energy_log)
    if len(daily_energy) > 0:
        daily_energy['date'] = pd.to_datetime(daily_energy['date'])
        daily_energy = daily_energy.sort_values('date')
        
        ax.plot(range(len(daily_energy)), daily_energy['total_energy_kwh'].values, 
                marker='o', linewidth=2.5, markersize=8, color='darkred', label='Daily Energy')
        ax.fill_between(range(len(daily_energy)), daily_energy['total_energy_kwh'].values, 
                        alpha=0.3, color='red')
        
        # Add average line
        avg_energy = daily_energy['total_energy_kwh'].mean()
        ax.axhline(y=avg_energy, color='green', linestyle='--', linewidth=2, label=f'Average: {avg_energy:.2f} kWh')
        
        ax.set_xlabel('Day', fontweight='bold')
        ax.set_ylabel('Energy Consumption (kWh)', fontweight='bold')
        ax.set_title('Daily Energy Consumption Trend', fontweight='bold', fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/report_project/fig_energy_trend.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_energy_trend.png")
    plt.close()
    
    # 5. System Architecture Diagram (text-based)
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.95, 'Smart Home Lighting System Architecture', 
            ha='center', fontsize=16, fontweight='bold', transform=ax.transAxes)
    
    # Components
    components = [
        ('Occupancy Sensors\n(Motion & Light)', 0.15, 0.75),
        ('Smart Lighting\nController', 0.5, 0.75),
        ('IoT Gateway\n& Cloud', 0.85, 0.75),
        ('User Dashboard\n& Mobile App', 0.5, 0.45),
        ('Energy Analytics\nEngine', 0.15, 0.45),
        ('Lighting Devices\n(Smart Bulbs)', 0.85, 0.45),
    ]
    
    for label, x, y in components:
        bbox = dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='black', linewidth=2)
        ax.text(x, y, label, ha='center', va='center', fontsize=11, fontweight='bold',
                transform=ax.transAxes, bbox=bbox)
    
    # Connections
    connections = [
        ((0.25, 0.75), (0.4, 0.75)),  # Sensors to Controller
        ((0.6, 0.75), (0.75, 0.75)),  # Controller to Gateway
        ((0.5, 0.65), (0.5, 0.55)),   # Gateway to Dashboard
        ((0.25, 0.65), (0.25, 0.55)), # Sensors to Analytics
        ((0.75, 0.65), (0.75, 0.55)), # Gateway to Devices
    ]
    
    for start, end in connections:
        ax.annotate('', xy=end, xytext=start, transform=ax.transAxes,
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # Features box
    features_text = 'Key Features:\n• Real-time Occupancy Detection\n• Automatic Light Control\n• Energy Optimization\n• Remote Access\n• Analytics & Reporting'
    ax.text(0.5, 0.15, features_text, ha='center', va='top', fontsize=10,
            transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='lightyellow', 
            edgecolor='black', linewidth=1.5))
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/report_project/fig_system_architecture.png', dpi=300, bbox_inches='tight')
    print("Saved: fig_system_architecture.png")
    plt.close()


def main():
    """Main execution function"""
    print("=" * 70)
    print("SMART HOME LIGHTING AUTOMATION SYSTEM SIMULATION")
    print("=" * 70)
    
    # Initialize system
    system = SmartHomeSystem()
    
    # Add rooms with different power ratings
    rooms_config = {
        'Living Room': 75,
        'Bedroom': 60,
        'Kitchen': 100,
        'Bathroom': 40,
        'Home Office': 65,
    }
    
    for room_name, power in rooms_config.items():
        system.add_room(room_name, power)
    
    print(f"\nSystem initialized with {len(rooms_config)} rooms:")
    for room in rooms_config.keys():
        print(f"  - {room}")
    
    # Simulate 7 days
    print("\nSimulating 7 days of operation...")
    all_data = []
    
    for day in range(7):
        simulation_date = datetime.now().date() - timedelta(days=6-day)
        daily_data = system.simulate_day(simulation_date)
        all_data.append(daily_data)
        
        daily_energy = daily_data.groupby('room')['energy_consumed_wh'].sum() / 1000
        print(f"Day {day+1}: Total Energy = {daily_data['energy_consumed_wh'].sum()/1000:.2f} kWh")
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    generate_visualizations(system, combined_data)
    
    # Generate report data
    report = system.get_system_report()
    
    print("\n" + "=" * 70)
    print("SYSTEM REPORT")
    print("=" * 70)
    print(f"Total Rooms: {report['total_rooms']}")
    print(f"Total Energy Consumed: {report['total_energy_kwh']:.2f} kWh")
    print(f"Average Daily Energy: {report['average_daily_energy_kwh']:.2f} kWh")
    print(f"Simulation Period: {report['simulation_days']} days")
    print("=" * 70)
    
    # Save data to CSV for reference
    combined_data.to_csv('/home/ubuntu/report_project/simulation_data.csv', index=False)
    print("\nSimulation data saved to: simulation_data.csv")
    
    # Save report to JSON
    report_json = {
        'system_report': report,
        'rooms': list(rooms_config.keys()),
        'simulation_date': datetime.now().isoformat(),
        'daily_energy_log': system.daily_energy_log
    }
    
    with open('/home/ubuntu/report_project/system_report.json', 'w') as f:
        json.dump(report_json, f, indent=2, default=str)
    
    print("System report saved to: system_report.json")
    
    return system, combined_data


if __name__ == "__main__":
    system, data = main()
