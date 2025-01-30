import eel
import sqlite3
import requests



# Initialize Eel
eel.init('web')

class User:
    def __init__(self,user_id, name, email, phone_number, dob, gender, address,password,payment_method):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone_number = phone_number
        self.dob = dob
        self.gender = gender
        self.address = address
        self.password = password
        self.payment_method = payment_method

    @staticmethod
    def create_user_table():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users ( 
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone_number TEXT NOT NULL UNIQUE,
        dob TEXT NOT NULL,
        gender TEXT NOT NULL CHECK(gender IN ('male','female','prefer not to say')),
        address TEXT NOT NULL,
        password TEXT NOT NULL
        )''')
        conn.commit()
        conn.close()




    @staticmethod
    @eel.expose
    def register_user(name, email, phone_number, dob, gender, address,password,confirm_password):

        if not name or not email or not phone_number or not dob or not gender or not address:
            return "All field are required"

        if password != confirm_password :
            return "Passwords do not match, try again"

        conn = None
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM users WHERE email=?', (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                return "Account already exists. please login"
            else:
                cursor.execute(
                    'INSERT INTO users (name, email, phone_number, dob, gender, address, password) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (name, email, phone_number, dob, gender, address, password))
                conn.commit()
                return "User registered successfully"

        except sqlite3.Error as e:
            return {"Status": "Error", "message": f"Database error: {str(e)}"}

        finally:
            conn.close()



    @staticmethod
    @eel.expose
    def login_function(email, password):

        if not email or not password:
            return "Both field are required"
        try:
             conn = sqlite3.connect('database.db')
             cursor = conn.cursor()
             cursor.execute('SELECT * FROM users WHERE email=?', (email,))
             user = cursor.fetchone()


             if user is None:
                 conn.close()
                 return "User not found"
             if password==user[7]:
                 user_data = {
                     'user_id':user[0],
                     'username': user[1],
                     'email': user[2],
                     'phone_number': user[3],
                     'dob': user[4],
                     'address': user[6],
                 }
                 conn.close()
                 return {"status":"Successful","user_data":user_data}

             else:
                return "Incorrect password, try again"

        except sqlite3.Error as e:
            # Handle database errors
            return {"status": "Error", "message": f"Database error: {str(e)}"}





class RideRequest:
    #Represents a ride request and manages booking operations for users.
    def __init__(self,request_id, user, pickup_location, drop_off_location, pickup_date, drop_off_date):
        self.request_id = request_id
        self.user = user
        self.pickup_location = pickup_location
        self.drop_off_location = drop_off_location
        self.pickup_date = pickup_date
        self.drop_off_date = drop_off_date

    @staticmethod
    def create_booking_table():
        conn = sqlite3.connect('database.db')
        conn.execute('PRAGMA foreign_keys=ON;')  # Enable foreign key support
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS booking_table (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        driver_id INTEGER,
        pickup_location TEXT NOT NULL,
        drop_off_location TEXT NOT NULL,
        pickup_date DATE NOT NULL,
        pickup_time TIMESTAMP NOT NULL,
        distance REAL NOT NULL,
        duration REAL NOT NULL,
        fare TEXT NOT NULL,
        booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        FOREIGN KEY (driver_id) REFERENCES drivers (driver_id)
        )''')
        conn.commit()
        conn.close()

    @staticmethod
    @eel.expose
    def insert_into_booking_table(user_id,driver_id, pickup_location, drop_off_location,pickup_date,pickup_time, distance, duration, fare):
        ##Insert a new booking into the booking table with the specified details.
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO booking_table (user_id,driver_id, pickup_location, drop_off_location,pickup_date, pickup_time,distance, duration, fare ) VALUES (?,?,?,?,?,?,?,?,?)',(user_id,driver_id, pickup_location, drop_off_location,pickup_date,pickup_time, distance, duration, fare))
        conn.commit()
        conn.close()
        return "Booking table inserted successfully"




    """
    This get_coordinates(pickup_location, drop_off_location): method retrieves geographical coordinates for the specified pickup and drop-off locations using the Mapbox API. 
    It calculates the route between the two locations, returning the distance, duration, and fare estimates. 
    If any errors occur during the API requests, it returns "Unavailable" for distance, duration, and fare, while maintaining the original locations. 
    But if you can't confirm your booking into GUI, 
    it will be more likely , mapbox site is down or you may have a network related issues.
    however. still you will get a pop into GUI indicating where is the issue
    """
    @staticmethod
    @eel.expose
    def get_coordinates(pickup_location, drop_off_location):
        if not pickup_location or not drop_off_location:
            return {"Status": "Error", "message": "Both fields are required"}

        mapbox_token = 'pk.eyJ1Ijoia2FzZW0ta2FzZW0iLCJhIjoiY20zdG90ZmR6MGFlczJqc2ZpZHdsZTFpciJ9.-Is3kDzfnvVyFT4Cjn8iHg' #mapbox token

        # Create URLs for pickup and drop-off location geocoding
        pickup_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{pickup_location}.json?access_token={mapbox_token}"
        drop_off_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{drop_off_location}.json?access_token={mapbox_token}"

        try:
            # Get coordinates for pickup location
            pickup_response = requests.get(pickup_url)
            if pickup_response.status_code != 200:
                return {"Status": "Error",
                        "message": f"Failed to fetch pickup location. Status code: {pickup_response.status_code}"}
            pickup_data = pickup_response.json()
            if not pickup_data['features']:
                return {"Status": "Error", "message": "Invalid pickup location"}
            pickup_coordinates = pickup_data['features'][0]['geometry']['coordinates']

            # Get coordinates for drop-off location
            drop_off_response = requests.get(drop_off_url)
            if drop_off_response.status_code != 200:
                return {"Status": "Error","message": f"Failed to fetch drop-off location. Status code: {drop_off_response.status_code}"}
            drop_off_data = drop_off_response.json()
            if not drop_off_data['features']:
                return {"Status": "Error", "message": "Invalid drop-off location"}
            drop_off_coordinates = drop_off_data['features'][0]['geometry']['coordinates']
            """
            Example JSON Response from Mapbox Geocoding API:
            {
                "type": "FeatureCollection",
                "query": ["New York"],
                "features": [
                            {
                                "id": "address.12345678901234567",
                                "type": "Feature",
                                "place_type": ["address"],
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [-74.006, 40.7128]
                                }
                            }
                        ]
            """
            # Use the coordinates to calculate directions
            mapbox_url = "https://api.mapbox.com/directions/v5/mapbox/driving"
            directions_url = f"{mapbox_url}/{pickup_coordinates[0]},{pickup_coordinates[1]};{drop_off_coordinates[0]},{drop_off_coordinates[1]}?access_token={mapbox_token}"

            # Request directions
            directions_response = requests.get(directions_url)
            if directions_response.status_code != 200:
                return {"Status": "Error",
                        "message": f"Failed to fetch directions. Status code: {directions_response.status_code}"}

            directions_data = directions_response.json()
            if not directions_data.get('routes'):
                return {"Status": "Error", "message": "No route found between locations"}

            # Calculate distance, duration, and fare
            distance = directions_data['routes'][0]['distance'] / 1000  # Convert meters to kilometers
            duration = directions_data['routes'][0]['duration'] / 60  # Convert seconds to minutes
            fare = distance * duration * 0.2  # Fare calculation logic

            # Return the calculated data
            return {
                    "Status": "Success",
                    "pickup_location":pickup_location,
                    "drop_off_location":drop_off_location,
                    "Distance": round(distance, 2),  # Distance in km
                    "Duration": round(duration, 2),  # Duration in minutes
                    "Fare": round(fare, 2)  #
                }


        except requests.exceptions.RequestException:
            #return these data, incase mapbox site is down or there is a network related issue
            return {
                "Status": "Success",
                "pickup_location": pickup_location,
                "drop_off_location": drop_off_location,
                "Distance": "Unavailable",
                "Duration": "Unavailable",
                "Fare": "Unavailable"
            }


    @staticmethod
    @eel.expose
    def booking_history(user_id):
        #Retrieve and return the booking history for a specified user.
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT booking_date, pickup_location, drop_off_location, pickup_date,pickup_time, fare,status FROM booking_table WHERE user_id=?',
                (user_id,))
            booking = cursor.fetchall()


            # Check if booking history is empty
            if len(booking) == 0:
                return "You don't have any booking history."

            else:
                # Return the result as a list of dictionaries (one for each booking)
                return {
                    "Bookings": [
                        {
                            "Booking Date": row[0],
                            "Pickup Location": row[1],
                            "Drop Off Location": row[2],
                            "Pickup Date": row[3],
                            "Pickup Time": row[4],
                            "Fare": row[5],
                            "Status": row[6]
                        }
                        for row in booking
                    ],
                }

        except sqlite3.Error as e:
            return {"Status": "Error", "message": str(e)}

    @staticmethod
    @eel.expose
    def active_booking(user_id):
        #Retrieve and return all active bookings for a specified user.
        try:
            # Establish a connection to the database
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()

                # Execute the query to fetch active bookings
                cursor.execute('''SELECT request_id, booking_date, pickup_location, drop_off_location, pickup_date, pickup_time, fare, status
                                  FROM booking_table
                                  WHERE user_id = ? AND (status = 'Active' OR status= 'Assigned' OR status = 'Driver Assigned') ''', (user_id,))
                active_booking = cursor.fetchall()

                # If no bookings are found, return a message
                if not active_booking:
                    return "You don't have any active bookings."

                # Process the result into a list of dictionaries
                booking_list = []
                for row in active_booking:
                    booking_list.append({
                        "request_id": row[0],
                        "booking_date": row[1],
                        "pickup_location": row[2],
                        "drop_off_location": row[3],
                        "pickup_date": row[4],
                        "pickup_time": row[5],
                        "fare": row[6],
                        "status": row[7]
                    })

                # Return the list of bookings
                return booking_list

        except sqlite3.Error as e:
            # Handle database-related errors
            print(f"Database error: {e}")
            return "An error occurred while fetching your bookings. Please try again later."

        except Exception as e:
            # Handle unexpected errors
            print(f"Unexpected error: {e}")
            return "An unexpected error occurred. Please try again later."

    @staticmethod
    @eel.expose
    def cancel_booking(request_id):
        #Cancel a booking with the specified request ID, if it's active.
        print(f"Canceling booking with request_id: {request_id}")
        try:
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE booking_table
                    SET status = 'Cancelled'
                    WHERE request_id = ? AND status IN ('Active', 'Driver Assigned','Assigned')
                ''', (request_id,))

                if cursor.rowcount > 0:
                    conn.commit()
                    return "Success"
                else:
                    print("No matching active booking found to cancel.")
                    return "No matching active booking found to cancel."

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "Database error. Please try again."

        except Exception as e:
            print(f"Unexpected error: {e}")
            return "Unexpected error occurred. Please try again."


class admin:
    def __init__(self, admin_id, name, email, phone, password):
        self.admin_id = admin_id
        self.name = name
        self.email = email
        self.phone = phone
        self.password = password

    @staticmethod
    def create_admin_table():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS admin (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        password TEXT
        )''')
        conn.commit()
        conn.close()

    @staticmethod
    @eel.expose
    def admin_login(email, password):
        #Authenticate an admin based on email and password
        if not email or not password:
            return "Both Fields are Required"
        else:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM admin WHERE email = ?', (email,))
                admin = cursor.fetchone()

                if admin is None:
                    return "No admin found. please register first"
                elif password == admin[4]:
                    return "Login Successful"
                else:
                    return "Incorrect Password, please try again"
            except sqlite3.OperationalError:
                return "Could not connect to admin database. Please try again"

    @staticmethod
    @eel.expose
    def admin_register(name, email, phone, password,confirmPassword):
        #Register a new admin in the database. Passwords must match.
        if password != confirmPassword:
            return "Passwords do not match"
        else:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM admin WHERE email = ?', (email,))
                existing_admin = cursor.fetchone()

                if existing_admin:
                    return "Email already registered. Please Login"
                else:
                    cursor.execute('INSERT INTO admin (name, email, phone, password) values (?, ?, ?, ?)', (name, email, phone, password))
                    conn.commit()
                    conn.close()
                    return "Admin Registration Successful"
            except sqlite3.OperationalError:
                return "Could not connect to admin database. Please try again"

    @staticmethod
    @eel.expose
    def admin_active_booking_dashboard():
        #"Retrieve and display all active bookings from the booking table.
        try:
               with sqlite3.connect('database.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('''SELECT * 
                                      FROM booking_table
                                      WHERE status ='Active' ''')
                    current_active_booking = cursor.fetchall()


                    if not current_active_booking :
                        return "No active bookings."
                    else:
                        print("Active bookings:")
                        active_bookings_as_arrays = [list(booking) for booking in current_active_booking]  # Convert each tuple to a list
                        for booking in active_bookings_as_arrays:
                            print(booking)  # Print each booking as a list
                        return active_bookings_as_arrays  # Return the list of arrays


        except sqlite3.Error as e:
            print(f"Database error: {e}")



    @staticmethod
    @eel.expose
    def get_available_drivers():
        #Retrieve and return a list of available drivers from the database.
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT driver_id, name, email, phone, vehicle_number_plate, license_number, status  FROM driver WHERE status = 'Available' ''')
        current_drivers = cursor.fetchall()

        if not current_drivers:
            return "No available drivers."
        else:
            print(current_drivers)
            current_drivers_as_arrays = [list(driver) for driver in current_drivers]
            for driver in current_drivers_as_arrays:
                print(driver)
                return current_drivers_as_arrays



    @staticmethod
    @eel.expose
    def get_all_drivers():
        #Retrieve and return a list of all drivers from the database.
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT driver_id, name, email, phone, vehicle_number_plate, license_number, status  FROM driver  ''')
        current_drivers = cursor.fetchall()

        if not current_drivers:
            return "No drivers."
        else:
            print(current_drivers)
            current_drivers_as_arrays = [list(driver) for driver in current_drivers]
            for driver in current_drivers_as_arrays:
                print(driver)
                return current_drivers_as_arrays





class driver:
    def __init__(self, driver_id, name, email, phone, vehicle_number_plate, license_number, password):
        self.driver_id = driver_id
        self.name = name
        self.email = email
        self.phone = phone
        self.vehicle_number_plate = vehicle_number_plate
        self.license_number = license_number
        self.password = password


    @staticmethod
    def create_driver_table():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS driver (
        driver_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        vehicle_number_plate TEXT,
        license_number TEXT,
        password TEXT,
        status DEFAULT 'Available'
        )''')
        conn.commit()
        conn.close()


    @staticmethod
    @eel.expose
    def driver_register(name, email, phone, vehicle_number_plate, license_number, password):
        #Register a new driver in the database. All fields are required
        if not name or not email or not phone or not vehicle_number_plate or not license_number or not password:
            return "All Fields are Required"
        else:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO driver(name, email, phone, vehicle_number_plate, license_number, password  )values (?,?,?,?,?,?)', (name, email, phone, vehicle_number_plate, license_number, password))
            conn.commit()
            conn.close()
            return "Driver Registration Successful"




    @staticmethod
    @eel.expose
    def driver_login(email, password):
        #Authenticate a driver based on email and password.
        if not email or not password:
            return "Both Fields are Required"
        else:
            try:
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM driver WHERE email = ?', (email,))
                driver = cursor.fetchone()

                if driver is None:
                    return "No Driver found. Please register first"
                elif password == driver[6]:
                    driver_data ={
                        "driver_id":driver[0],
                        "name":driver[1],
                        "email":driver[2],
                        "phone":driver[3],
                        "vehicle_number_plate":driver[4],
                        "license_number":driver[5],
                        "status":driver[7],
                    }
                    return {"Login":"Login Successful","driver_data":driver_data}
                else:
                    return "Incorrect Password, please try again"
            except sqlite3.Error as e:
                print(f"Database error: {e}")

    @staticmethod
    @eel.expose
    def assign_driver(booking_id, driver_id):
        #Assign a driver to a booking based on booking ID.
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Update booking table to assign driver to the booking
            cursor.execute('''UPDATE booking_table SET driver_id = ?, status = 'Driver Assigned' WHERE request_id = ? AND status = 'Active' ''',
                           (driver_id, booking_id))
            conn.commit()

            # Check if any row was updated
            if cursor.rowcount > 0:
                conn.close()
                return "Driver successfully assigned"
            else:
                conn.close()
                return "Booking not found or status is not active"

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return f"Database error: {e}"

        except Exception as e:
            print(f"Unexpected error: {e}")
            return f"Unexpected error: {e}"



    @staticmethod
    @eel.expose
    def change_driver_status(driver_id, status):
        #Change the status of a driver identified by driver_id.
        conn = None
        try:
            # Establish a connection to the database
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Execute the update query to change driver status
            cursor.execute('''UPDATE driver SET status = ? WHERE driver_id = ?''', (status, driver_id))
            conn.commit()

            # Check if any row was updated
            if cursor.rowcount > 0:
                return "Driver Status Updated"  # Success message
            else:
                return "No changes made to Driver Status"  # No rows updated (likely driver_id not found or status was the same)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return f"Database error: {e}"  # Return the error message to frontend

        except Exception as e:
            print(f"Unexpected error: {e}")
            return f"Unexpected error: {e}"  # Return any unexpected errors to frontend

        finally:
            # Ensure that the connection is closed even if there is an error
            if conn:
                conn.close()


    @staticmethod
    @eel.expose
    def show_assign_trip(driver_id):
        #Retrieve and show assigned trips for a given driver ID.
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Use the driver_id parameter in the query
            cursor.execute('''SELECT * FROM booking_table WHERE driver_id = ? AND status = 'Driver Assigned' ''',
                           (driver_id,))
            assigned_driver_task = cursor.fetchall()  # Fetch all matching rows

            if not assigned_driver_task:  # Check if no rows are returned
                conn.close()
                return "No Assigned Trip"
            else:
                # Prepare the result list to return
                assigned_driver_task_as_list = [list(task) for task in assigned_driver_task]
                for task in assigned_driver_task_as_list:
                    print(task)  # Print each task
                conn.close()
                return assigned_driver_task_as_list  # Return the list of tasks
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    @staticmethod
    @eel.expose
    def complete_trip(driver_id):
        #Complete the trip for the assigned driver.
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Update booking table to complete the booking
            cursor.execute(
                '''UPDATE booking_table SET  status = 'completed' WHERE driver_id = ? AND status = 'Driver Assigned' ''',
                (driver_id,))
            conn.commit()
            conn.close()
            return "Completed Trip"
        except sqlite3.Error as e:
            print(f"Database error: {e}")




User.create_user_table()
admin.create_admin_table()
RideRequest.create_booking_table()
driver.create_driver_table()
def main():


    # Start the Eel application
    eel.start('/html/login.html', size=(620, 800), block=True)


# Run the main function
if __name__ == '__main__':
    main()
