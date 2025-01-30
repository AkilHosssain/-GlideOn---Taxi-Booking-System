document.addEventListener("DOMContentLoaded", async function () {
    console.log("JavaScript is loaded and running!");

    // =========================
    // User Registration and Login
    // =========================

    // User Registration
    handleFormSubmit("registrationForm", async () => {
        const name = document.getElementById("registerUsername").value.trim();
        const email = document.getElementById("email").value.trim();
        const number = document.getElementById("number").value.trim();
        const dob = document.getElementById("dob").value.trim();
        const gender = document.querySelector('input[name="gender"]:checked')?.value.trim();
        const fullAddress = `${document.getElementById('address-line-1').value.trim()}, 
                                    ${document.getElementById('address-line-2').value.trim()}, 
                                    ${document.getElementById('city').value.trim()}, 
                                    ${document.getElementById('region').value.trim()}, 
                                    ${document.getElementById('country').value.trim()}, 
                                    ${document.getElementById('postal-code').value.trim()}`;
        const password = document.getElementById("password").value.trim();
        const confirmPassword = document.getElementById("confirmPassword").value.trim();

        try {
            const result = await eel.register_user(name, email, number, dob, gender, fullAddress, password, confirmPassword)();
            if (result === "User registered successfully") {
                alert(result);
                window.location.href = "login.html"; // Redirect to login page

            } else {
                alert(result); // Show error message
            }
        } catch (error) {
            console.error("Error during user registration:", error);
            alert("An error occurred. Please try again.");
        }
    });

    // User Login
    handleFormSubmit("loginForm", async () => {
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value.trim();
        try {
            const result = await eel.login_function(email, password)();
            if (result.status === "Successful") {
                alert("Login Successful");
                sessionStorage.setItem("user_data", JSON.stringify(result.user_data)); // Store user data
                window.location.href = "/html/dashboard.html"; // Redirect to dashboard
            } else {
                alert(result); // Show error message
            }
        } catch (error) {
            console.error("Error during login:", error);
            alert("login_function didn't connect. Please try again.");
        }
    });

    // User Dashboard
    const dashboard = document.getElementById("dashboard");
    if (dashboard) {
        dashboard.addEventListener("submit", async function (event) {
            event.preventDefault(); // Prevent default form submission
            const pickup_location = document.getElementById("pickup").value.trim();
            const drop_off_location = document.getElementById("dropoff").value.trim();
            const booking_date = document.getElementById("scheduleDate").value.trim();
            const booking_time = document.getElementById("scheduleTime").value.trim();

            // Store booking date and time in sessionStorage
            sessionStorage.setItem("booking_date", booking_date);
            sessionStorage.setItem("booking_time", booking_time);
            try {
                const result = await eel.get_coordinates(pickup_location, drop_off_location)();
                if (result.Status === "Success") {
                    localStorage.setItem("rideDetails", JSON.stringify(result)); // Store ride details
                    window.location.href = "trip-details.html"; // Redirect to trip details page
                } else {
                    alert(`Error: ${result.message}`); // Show error message
                }
            } catch (error) {
                console.error("Error fetching coordinates:", error);
                alert("There was an error fetching the coordinates.");
            }
        });
    }

    // Trip Details Page
    const resultContainer = document.getElementById("resultContainer");
    if (resultContainer) {
        const rideDetails = JSON.parse(localStorage.getItem("rideDetails"));
        if (rideDetails) {
            document.getElementById("distance").textContent = `Distance: ${rideDetails.Distance} km`;
            document.getElementById("duration").textContent = `Duration: ${rideDetails.Duration} minutes`;
            document.getElementById("fare").textContent = `Fare: $${rideDetails.Fare}`;
        } else {
            resultContainer.textContent = "No ride details found!";
        }
    }

    // Confirm Order Button
    const ConfirmOrderButton = document.getElementById("confirmOrder");
    if (ConfirmOrderButton) {
        ConfirmOrderButton.addEventListener("click", async function (event) {
            event.preventDefault(); // Prevent default button action
            const rideDetails = JSON.parse(localStorage.getItem("rideDetails"));
            const user_data = JSON.parse(sessionStorage.getItem("user_data"));
            const booking_date = sessionStorage.getItem("booking_date");
            const booking_time = sessionStorage.getItem("booking_time");

            if (rideDetails) {
                const user_id = user_data.user_id;
                const driver_id = "Not Assigned"; // Default driver status
                const pickupLocation = rideDetails.pickup_location;
                const dropOffLocation = rideDetails.drop_off_location;
                const distance = rideDetails.Distance;
                const duration = rideDetails.Duration;
                const fare = rideDetails.Fare;

                try {
                    const result = await eel.insert_into_booking_table(user_id, driver_id, pickupLocation, dropOffLocation, booking_date, booking_time, distance, duration, fare)();
                    console.log(result);
                    window.location.href = "booking.html"; // Redirect to booking page
                } catch (error) {
                    console.error("Not connecting with insert_into_booking_table function", error);
                }
            }
        });
    }

    // Booking History Page
    const historyPage = document.getElementById("booking-history-container");
    if (historyPage) {
        const user_ID = JSON.parse(sessionStorage.getItem("user_data"));
        const user_id = user_ID ? user_ID.user_id : null;

        if (user_id) {
            const result = await eel.booking_history(user_id)();
            console.log(result);
            if (result && result.Bookings && result.Bookings.length > 0) {
                const tableBody = document.querySelector("#booking-history-table tbody");
                result.Bookings.forEach(booking => {
                    const row = document.createElement("tr");
                    Object.values(booking).forEach(value => {
                        const cell = document.createElement("td");
                        cell.textContent = value; // Populate cell with booking detail
                        row.appendChild(cell);
                    });
                    tableBody.appendChild(row); // Append the row to the table
                });
            } else {
                console.log("No bookings available.");
                const message = document.createElement("p");
                message.textContent = "No booking history.";
                historyPage.appendChild(message);
            }
        } else {
            console.log("User ID not found in session storage.");
        }
    } else {
        console.log("Booking history container not found.");
    }

    // Active Bookings on Booking Page
    const bookingPage = document.getElementById("bookingContainer");
    if (bookingPage) {
        const user_ID = JSON.parse(sessionStorage.getItem("user_data"));
        const user_id = user_ID ? user_ID.user_id : null;

        if (user_id) {
            eel.active_booking(user_id)((result) => {
                const tableBody = document.querySelector("#bookingTableBody");
                if (result && Array.isArray(result) && result.length > 0) {
                    tableBody.innerHTML = ""; // Clear previous content
                    result.forEach((booking) => {
                        const row = document.createElement("tr");
                        const bookingDateCell = document.createElement("td");
                        bookingDateCell.textContent = booking.booking_date;
                        row.appendChild(bookingDateCell);
                        const pickupLocationCell = document.createElement("td");
                        pickupLocationCell.textContent = booking.pickup_location;
                        row.appendChild(pickupLocationCell);
                        const dropOffLocationCell = document.createElement("td");
                        dropOffLocationCell.textContent = booking.drop_off_location;
                        row.appendChild(dropOffLocationCell);
                        const pickupDateCell = document.createElement("td");
                        pickupDateCell.textContent = booking.pickup_date;
                        row.appendChild(pickupDateCell);
                        const pickupTimeCell = document.createElement("td");
                        pickupTimeCell.textContent = booking.pickup_time;
                        row.appendChild(pickupTimeCell);
                        const fareCell = document.createElement("td");
                        fareCell.textContent = booking.fare;
                        row.appendChild(fareCell);
                        const statusCell = document.createElement("td");
                        statusCell.textContent = booking.status;
                        row.appendChild(statusCell);

                        // Create a cell for the "Cancel" button
                        const actionCell = document.createElement("td");
                        const cancelButton = document.createElement("button");
                        cancelButton.textContent = "Cancel"; // Button to cancel the booking
                        cancelButton.classList.add("cancel-booking-button");
                        cancelButton.addEventListener("click", () => {
                            console.log("Cancel clicked for:", booking);
                            eel.cancel_booking(booking.request_id)((response) => {
                                if (response === "Success") {
                                    alert("Booking has been cancelled.");
                                    row.remove(); // Optionally remove the row from the table
                                } else {
                                    alert("Error cancelling booking.");
                                }
                            }).catch((error) => {
                                console.error("Error during cancellation:", error);
                                alert("An unexpected error occurred.");
                            });
                        });
                        actionCell.appendChild(cancelButton); // Append the cancel button to the action cell
                        row.appendChild(actionCell); // Append the action cell to the row
                        tableBody.appendChild(row); // Append the row to the table body
                    });
                } else {
                    console.log("No active bookings available.");
                    const message = document.createElement("p");
                    message.textContent = "No active bookings.";
                    tableBody.appendChild(message);
                }
            }).catch((error) => {
                console.error("Error fetching active bookings:", error);
            });
        } else {
            console.log("User ID not found in session storage.");
        }
    } else {
        console.log("Booking container not found.");
    }

    // =========================
    // Admin Registration and Login
    // =========================

    // Admin Registration
    handleFormSubmit("registration-form", async () => {
        const name = document.getElementById("fullName").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const password = document.getElementById("password").value.trim();
        const confirmPassword = document.getElementById("confirmPassword").value.trim();

        try {
            const result = await eel.admin_register(name, email, phone, password, confirmPassword)();
            alert(result);
            if (result === "Admin Registration Successful") {
                window.location.href = "admin login page.html"; // Redirect to admin login page
            }
        } catch (error) {
            console.error("Couldn't connect to admin_register page", error);
            alert("Couldn't connect to admin_register page");
        }
    });

    // Admin Login
    handleFormSubmit("admin-login", async () => {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();

        try {
            const result = await eel.admin_login(email, password)();
            alert(result);
            if (result === "Login Successful") {
                window.location.href = "admin-dashboard.html"; // Redirect to admin dashboard
            }
        } catch (error) {
            console.error("Error occurred while calling admin login function", error);
        }
    });

    // Admin Dashboard
    if (window.location.pathname.includes("admin-dashboard.html")) {
        try {
            const result = await eel.admin_active_booking_dashboard()();
            const result2 = await eel.get_all_drivers()();
            const bookingTableBody = document.getElementById("bookingsTableBody");
            bookingTableBody.innerHTML = ""; // Clear existing content

            const AvailableDriverTableBody = document.getElementById("AvailableDriverTableBody");
            AvailableDriverTableBody.innerHTML = ""; // Clear existing content for available drivers

            if (typeof result === "string" && result === "No active bookings.") {
                bookingTableBody.innerHTML = "<tr><td colspan='12'>No Active Booking At the moment.</td></tr>";
            } else {
                result.forEach(item => {
                    const row = document.createElement("tr");
                    item.forEach((cell, index) => {
                        const cellElement = document.createElement("td");
                        if (index === item.length - 1) {
                            const button = document.createElement("button");
                            button.textContent = "Assign Driver"; // Button to assign a driver
                            button.onclick = () => openDriverModal(item[0]); // Pass booking ID
                            cellElement.appendChild(button);
                        } else {
                            cellElement.textContent = cell; // Populate cell with data
                        }
                        row.appendChild(cellElement);
                    });
                    bookingTableBody.appendChild(row); // Append row to the table
                });
            }

            if (result2.length === 0) {
                AvailableDriverTableBody.innerHTML = "<tr><td colspan='8'>No Available Drivers At the moment.</td></tr>";
            } else {
                result2.forEach(driver => {
                    const row2 = document.createElement("tr");
                    driver.forEach(cell2 => {
                        const cell2Element = document.createElement("td");
                        cell2Element.textContent = cell2; // Populate cell with driver data
                        row2.appendChild(cell2Element);
                    });
                    AvailableDriverTableBody.appendChild(row2); // Append row to the table
                });
            }

        } catch (error) {
            console.error("Error fetching active bookings:", error);
            const bookingTableBody = document.getElementById("bookingsTableBody");
            bookingTableBody.innerHTML = "<tr><td colspan='12'>Error loading bookings.</td></tr>";
        }
    }

    // Modal for Assigning Driver
    function openDriverModal(bookingId) {
        const modal = document.getElementById("assignDriverModal");
        modal.style.display = "block"; // Show the modal

        // Fetch available drivers for assignment
        eel.get_available_drivers()(drivers => {
            const driverSelect = document.getElementById("driverSelect");
            driverSelect.innerHTML = ""; // Clear existing options

            // Populate the driver selection dropdown
            drivers.forEach(driver => {
                const option = document.createElement("option");
                option.value = driver[0]; // Use ID as the value
                option.textContent = driver[1]; // Display Name in dropdown
                driverSelect.appendChild(option);
            });


            // Confirm assignment button
            document.getElementById("confirmAssignButton").onclick = async () => {
            const selectedDriverId = driverSelect.value; // Get selected driver ID
            try {
                // Assign the driver to the booking
                const updateResult = await eel.assign_driver(bookingId, selectedDriverId)();

                // Check if the result from assign_driver is a success message
                if (updateResult === "Driver successfully assigned") {
                    // Update the driver status to 'Unavailable'
                    const statusResult = await eel.change_driver_status(selectedDriverId, 'Unavailable')();

                    // Check if the status update was successful
                    if (statusResult === "Driver Status Updated") {
                        modal.style.display = "none"; // Close the modal
                        alert("Driver successfully assigned and status updated to Unavailable!");
                    } else {
                        alert("Error updating driver status: " + statusResult);
                    }
                } else {
                    alert("Error assigning driver: " + updateResult);
                }
            } catch (error) {
                console.error("Error assigning driver or updating status:", error);
                alert("An unexpected error occurred while assigning the driver or updating the status.");
            }
        };


            // Cancel button to close the modal
            document.getElementById("cancelAssignButton").onclick = () => {
                modal.style.display = "none"; // Close the modal
            };
        });
    }

    // =========================
    // Driver Registration and Login
    // =========================

    // Driver Registration
    handleFormSubmit("driverRegisterForm", async () => {
        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const vehicleNumberPlate = document.getElementById("vehicle_number_plate").value.trim();
        const licenseNumber = document.getElementById("license_number").value.trim();
        const password = document.getElementById("password").value.trim();

        try {
            const result = await eel.driver_register(name, email, phone, vehicleNumberPlate, licenseNumber, password)();
            console.log(result);
            window.location.href = "/html/driver-login.html"; // Redirect to driver login page
        } catch (error) {
            console.log("Error Registering Driver:", error);
        }
    });

    // Driver Login
    handleFormSubmit("driver-login-form", async () => {
        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value.trim();
        try {
            const result = await eel.driver_login(email, password)();
            if (result.Login === "Login Successful") {
                sessionStorage.setItem("driver_data", JSON.stringify(result.driver_data)); // Store driver data
                window.location.href = "/html/driver-dashboard.html"; // Redirect to driver dashboard
            } else {
                alert(result); // Show error message
            }
        } catch (error) {
            console.error("Error during driver login:", error);
            alert("Error occurred during login. Please try again.");
        }
    });

    // Driver Dashboard
    if (window.location.pathname.includes("driver-dashboard.html")) {
        const driverData = JSON.parse(sessionStorage.getItem("driver_data")); // Retrieve driver data
        if (driverData) {
            document.getElementById("driver-id").textContent = driverData.driver_id;
            document.getElementById("name").textContent = driverData.name;
            document.getElementById("email").textContent = driverData.email;
            document.getElementById("phone").textContent = driverData.phone;
            document.getElementById("vehicle-number-plate").textContent = driverData.vehicle_number_plate;
            document.getElementById("license-number").textContent = driverData.license_number;
            document.getElementById("status").textContent = driverData.status;

            fetchAssignedTrips(driverData.driver_id); // Fetch trips assigned to the driver
        } else {
            console.log("Driver data not retrieved");
        }

        const statusToggle = document.getElementById("status-toggle");
        if (statusToggle) {
            statusToggle.addEventListener("click", toggleOnlineStatus); // Add event listener to toggle driver status
        }

        async function toggleOnlineStatus() {
            const statusText = document.getElementById("status-text");
            const driverId = driverData.driver_id; // Get driver ID
            const newStatus = statusToggle.checked ? "Available" : "Unavailable"; // Determine new status

            try {
                const result = await eel.change_driver_status(driverId, newStatus)();
                if (result === "Driver Status Updated") {
                    document.getElementById("status").textContent = newStatus; // Update status on UI
                        statusText.textContent = newStatus === "Available" ? "Go Offline" : "Go Online"; // Update toggle label
                } else {
                    alert("Failed to update driver status.");
                }
            } catch (error) {
                console.error("Error changing driver status:", error);
                alert("Error updating status. Please try again.");
            }
        }

        // Attach completeTrip to the global window object
window.completeTrip = async function(tripId) {
    const driver_data = JSON.parse(sessionStorage.getItem("driver_data"));
    const driver_id = driver_data.driver_id;

    try {
        const result = await eel.complete_trip(driver_id,)(); // Pass tripId to the backend
        console.log(result);
        if (result === "Completed Trip") {

            alert("Thanks for completing the trip")
            // Refresh assigned trips
            fetchAssignedTrips(driver_id);
        } else {
            alert("Failed to complete the trip. Please try again.");
        }
    } catch (error) {
        console.log("Error completing the trip:", error);
        alert("Error occurred while completing the trip. Please try again.");
    }
};

// Function to fetch assigned trips
async function fetchAssignedTrips(driverId) {
    try {
        const result = await eel.show_assign_trip(driverId)();
        const tripStatusTable = document.getElementById("trip-status-body"); // Reference the new tbody ID
        tripStatusTable.innerHTML = ""; // Clear previous trip status

        if (Array.isArray(result) && result.length > 0) {
            result.forEach(task => {
                const row = tripStatusTable.insertRow();
                row.innerHTML = `
                    <td>${task[0]}</td> <!-- Task ID -->
                    <td>${task[1]}</td> <!-- Booking ID -->
                    <td>${task[2]}</td> <!-- Driver ID -->
                    <td>${task[3]}</td> <!-- Pick-up Location -->
                    <td>${task[4]}</td> <!-- Drop-off Location -->
                    <td>${task[5]}</td> <!-- Date -->
                    <td>${task[6]}</td> <!-- Time Assigned -->
                    <td>${task[7]}</td> <!-- Distance -->
                    <td>${task[8]}</td> <!-- Duration -->
                    <td>${task[9]}</td> <!-- Fare -->
                    <td>${task[10]}</td> <!-- Assigned Time -->
                    <td><button onclick="completeTrip('${task[0]}')">Complete Trip</button></td> <!-- Action -->
                `;
            });
        } else {
            tripStatusTable.innerHTML = "<tr><td colspan='12'>No Assigned Trip</td></tr>";
        }
    } catch (error) {
        console.log("Error fetching assigned trips:", error);
    }
}
    }


    // =========================
    // Common Functions
    // =========================

    // Function to handle form submissions
    function handleFormSubmit(formId, callback) {
        const form = document.getElementById(formId);
        if (form) {
            form.addEventListener("submit", async (event) => {
                event.preventDefault(); // Prevent default form submission
                await callback(); // Call the provided callback function
            });
        }
    }
});