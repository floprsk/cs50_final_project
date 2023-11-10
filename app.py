from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import sqlite3
import time
from threading import Thread
import signal
import sys
from crontab import CronTab



# Raspi Librarys
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO


# Raspi Configs
SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
port = 12




# Get data from humidity sensor as percentage
def sensor_info():
    try:
        hum = mcp.read_adc(0)
        per = ((585-int(hum))*100) / 285
        # 585 = minimal humidity
        # 300 = maximal humidity 
        # --> 285 = difference 
        return int(per)
    except:
        return None

# Turn waterpump off
# Using it on every route, to be sure that pump is off in the first place
def pump_off():
    # Everytime new GPIO.setmode() bc of GPIO.cleanup() 
    # Has to be done to ensure that no false GPIO signals are sent
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(port, GPIO.OUT)
    GPIO.output(port, 1)
    GPIO.cleanup()

# Clean exit when CTRL+C is hitted
def clean_exit(signal, frame):
    print("Handling SIGINT (CTRL+C)")
    pump_off()
    sys.exit(0)


# Checks if water level is too low
# If too low: Water pump is turned off
def float_switch():
    try:
        while True:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(21, GPIO.IN)

            is_full = GPIO.input(21)
            # If tank is empty
            if is_full == 1:
                GPIO.setup(port, GPIO.OUT)
                GPIO.output(port, 1)
                GPIO.cleanup()
                print("Tank is empty. Pumpe ausgeschaltet.")
            else:
                print("Tank is full")
            time.sleep(5)
    except Exception as e:
        pump_off()
        print("Fehler in float_switch Thread: ", e)


### Flask App ###

app = Flask(__name__)
# Configure application
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)


def start_flask():
    # On every start of app: pump_off()
    pump_off()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=8080)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    pump_off()

    # Connect with database
    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()
    # If not logged in yet --> index.html
    if session == None or not session or session["id"] == None:
        return render_template("index.html")
    else:
        all_plants = cur.execute(
            "SELECT * FROM plants WHERE user_id = ?", [session["id"]]).fetchall()
        watering_days = cur.execute(
            "SELECT * FROM watering_days WHERE user_id = ?", [session["id"]]).fetchall()
        humidity = sensor_info()

        # Update of plant-humidity Infos on reload (only working if sensor is installed, yet only for one sensor)
        cur.execute("UPDATE plants SET humidity = ? WHERE user_id == ? AND is_sensor == ?", [
                    humidity, session["id"], "on"])
        con.commit()

        # If logged in, return info_plant page
        return render_template("info_plant.html", plants=all_plants, days=watering_days, humidity=sensor_info(), session=session)


# Log user in
@app.route("/login", methods=["POST", "GET"])
def login():
    pump_off()
    # Forget any user_id
    session["id"] = None
    session["name"] = None
    
    # Connect with database
    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Collecting form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if username == None or not username:
            flash("No username provided.")
            return redirect("/")

        # Search database if user is already registered
        else:
            user_existing = cur.execute(
                "SELECT * FROM users WHERE name == ?", [username])
            user_existing = user_existing.fetchone()

            # Check if user already registered
            if user_existing == None or not user_existing:
                flash("Not registered yet.")
                return redirect("/")
            # Check if password was provided
            elif password == None or not password:
                flash("No password provided.")
                return redirect("/")
            # Check if passsword is correct
            elif not check_password_hash(user_existing[2], password):
                flash("Password incorrect.")
                return redirect("/")
            # If everything is fine:
            else:
                # Remember which user has logged in
                session["id"] = user_existing[0]
                session["name"] = user_existing[1]
                return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return redirect("/")

# Page to add plants to account (database)


@app.route("/adding_page", methods=["GET", "POST"])
def adding_page():
    pump_off()
    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()

    # If not logged in yet --> index-html
    if session == None or not session or session["id"] == None:
        return render_template("index.html")
    # If logged in and reached by GET or POST
    else:
        # Update
        all_plants = cur.execute(
            "SELECT * FROM plants WHERE user_id = ?", [session["id"]]).fetchall()
        watering_days = cur.execute(
            "SELECT * FROM watering_days WHERE user_id = ?", [session["id"]]).fetchall()
        humidity = sensor_info()
        # Update of plant-humidity Infos on reload (only working if sensor is installed, yet only for one sensor)
        cur.execute("UPDATE plants SET humidity = ? WHERE user_id == ? AND is_sensor == ?", [
                    humidity, session["id"], "on"])
        con.commit()
        # return adding_page
        # new route for that, so that adding_page is reached by (add) buttons
        # Bc i wanted the landing page to be info_plant.html (lookup "/" route)
        return render_template("adding_page.html", plants=all_plants, days=watering_days, humidity=sensor_info(), session=session)

# Log user out


@app.route("/logout")
def logout():
    pump_off()
    # Clear session data
    session["id"] = None
    session["name"] = None
    return redirect("/")


# Register new user account
@app.route("/register", methods=["GET", "POST"])
def register():
    pump_off()

    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()

    all_users = cur.execute("SELECT * FROM users")
    all_users = all_users.fetchall()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Collect data from forms
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Search database if username is already declarated to an account
        user_existing = cur.execute(
            "SELECT name FROM users WHERE name == ?", [username])
        user_existing = user_existing.fetchone()
        # user = ('username',)

        # Ensure correct user inputs
        if username == None or not username:
            flash("Choose a username.")
        # If username is free: (before username check, bc of type:None problem)
        elif user_existing == None:
            # Check if password provided and confirmed
            if password == None or not password:
                flash("Must provide a password.")
                return render_template("register.html", users=all_users)
            elif confirmation != password:
                flash("Password confirmation failed.")
            # If everything is fine:
            # Insert user into database with hashed password
            else:
                cur.execute("INSERT INTO users(name, password) VALUES(?, ?)", [
                            username, generate_password_hash(password, method='pbkdf2:sha1',salt_length=16 )])
                con.commit()
                con.close()
                flash("Succesfully registered!")
                return redirect("/login")
        # If username if already registered
        elif username == user_existing[0]:
            flash("Username already exists. Choose another one.")
        return render_template("register.html", users=all_users)
   

    # User reached route via GET
    else:
        flash("Choose a username and a password.")
        return render_template("register.html", users=all_users)


@app.route("/add_plant", methods=["GET", "POST"])
def addPlant():
    pump_off()

    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()
    # Crontab Schedule -> File on Raspberry Pi to schedule actions (watering, log_data)
    cron = CronTab(user='flopi')

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST" and session["name"] == "flo":
        # Collecting form data
        plant_name = request.form.get("plant_name")

        # if selected: Value = "on"
        is_sensor = request.form.get("is_sensor")
        is_waterpump = request.form.get(
            "is_waterpump")  # if not:      Value = None

        watering_amount = request.form.get("watering_amount")
        watering_time = request.form.get("watering_time")

        # Check if plant (name) already exists for that user
        plant_existing = cur.execute(
            "SELECT * FROM plants WHERE name == ? AND user_id == ?", [plant_name, session["id"]]).fetchone()
        # Collecting plant number (necesarry for info_plant.html)
        plant_number = cur.execute("SELECT COUNT() FROM plants WHERE user_id = ?", [
                                   session["id"]]).fetchone()

        selected_days = []
        # Iterate through weekday selector data and write data into list
        for day in range(1, 8):
            # weekday selector is build with explicit input names to detect the days which are selected
            # value of these inputs is 'Mon', 'Tue', 'Wed, ...
            form_field = 'dow' + str(day)
            if form_field in request.form:
                # Formatting selected_days in the right crontab-form
                # Example: ['Mon', 'Thu', 'Sun']
                selected_days.append(request.form.get(form_field))

        # Handle form inputs:
        if not selected_days:
            selected_days = None
        # If schedule is selected but no pump is selected
        elif is_waterpump == None:
            flash("No waterpump is installed, so no schedule can be selected.")
            return redirect("/adding_page")
        # Ensure that time is chosen when schedule is selected
        elif selected_days != None and (watering_time == None or not watering_time):
            flash("Select the time your plant should get watered.")
            return redirect("/adding_page")
        # Check if plant_name was given
        if plant_name == None or not plant_name:
            flash("What plant do you want to add?")
            return redirect("/adding_page")
        # If humidty sensor is selected -> data log activated
        

        
        # Check if plant already exists for that user
        if plant_existing == None or not plant_existing:
            # If everythings fine --> Insertion into users.db
            # First INSERTION into plants Table
            cur.execute("INSERT INTO plants(name, watering_schedule, user_id, is_sensor, is_waterpump, watering_time, watering_amount, plant_number) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", [
                        plant_name, str(selected_days), session["id"], is_sensor, is_waterpump, watering_time, watering_amount, (plant_number[0]+1)])
            con.commit()
            cur.execute("INSERT INTO watering_days(user_id) VALUES(?)", [
                        session["id"]])
            con.commit()

            # plants(id) is configured to auto increment, so get it per database query
            plant_id = cur.execute("SELECT id FROM plants WHERE name == ?", [
                                   plant_name]).fetchone()
            plant_id = plant_id[0]

            # Writing data of selected days in different table (watering_days)
            if selected_days != None:
                for day in selected_days:
                    if day == 'Mon':
                        cur.execute(
                            "UPDATE watering_days SET mon = ? WHERE plant_id = ?", [1, plant_id])
                    if day == 'Tue':
                        cur.execute(
                            "UPDATE watering_days SET tue = ? WHERE plant_id = ?", [1, plant_id])
                    if day == 'Wed':
                        cur.execute(
                            "UPDATE watering_days SET wed = ? WHERE plant_id = ?", [1, plant_id])
                    if day == 'Thu':
                        cur.execute(
                            "UPDATE watering_days SET thu = ? WHERE plant_id = ?", [1, plant_id])
                    if day == 'Fri':
                        cur.execute(
                            "UPDATE watering_days SET fri = ? WHERE plant_id = ?", [1, plant_id])
                    if day == 'Sat':
                        cur.execute(
                            "UPDATE watering_days SET sat = ? WHERE plant_id = ?", [1, plant_id])
                    if day == 'Sun':
                        cur.execute(
                            "UPDATE watering_days SET sun = ? WHERE plant_id = ?", [1, plant_id])

                # Bc Jinja problems with interpreting selected_days list
                # First step: Write data of plant in TABLE plants and create a row in TABLE watering_days for that user
                # Second step: UPDATE watering_days --> with INSERT it's not possible to use WHERE clause
                # watering_days structure:
                # plant_id | user_id | mon | tue | wed | thu | fri | sat | sun

                
                # Write new cron command into crontab-File on Raspi
                # Iterate through cron jobs and delete if theres already a schedule
                identifier_sched = 'schedule' + str(plant_id)
                for job in cron:
                    if job.comment == identifier_sched:
                        cron.remove(job)
                        cron.write()

                job1 = cron.new(command='python3 /home/flopi/Watering/Watering_app/sprinkle.py', comment = identifier_sched )
                job1.dow.on(*selected_days)
                job1.hour.on(watering_time)

                cron.write()

            if is_sensor != None:
                # Iterate through cron jobs and delete if theres already a sensor log
                identifier_data = 'data' + str(plant_id)
                for job in cron:
                    if job.comment == identifier_data:
                        cron.remove(job)
                        cron.write()
                job2 = cron.new(command='python3 /home/flopi/Watering/Watering_app/log_data.py', comment = identifier_data)
                job2.setall('0 12,0 * * *')       # Every 12 hours beginning from 12 AM
                cron.write()

            # Plant was added, redircetion to adding_page
            con.commit()
            flash("Plant was added to plant bed.")
            return redirect("/adding_page")

        # If plant existing for that user:
        if plant_existing:
            flash("Plant already exists in your plant bed.")
            return redirect("/adding_page")

    # User reached route via GET (as by submitting a form via GET)
    elif session["name"] != "flo":
        flash("No permissions to add plants.")
        return redirect("/adding_page")
    else:
        return redirect("/adding_page")


@app.route("/delete_plant", methods=["GET", "POST"])
def deletePlant():
    pump_off()

    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()
    cron = CronTab(user='flopi')

    if request.method == "POST" and session["name"] == "flo":
        # Collect form data
        # if form on adding_page.html was submitted
        plant_id = request.form.get("plant_id")
        # if form on info_plant.html was submitted
        plant_id_info = request.form.get("plant_id_info")

        # Remove all crontab commands, when one plant is deleted
        # COMING SOON: individual scheduling for different plants, yet it works properly for one plant only
        if session["name"] == "flo":
            identifier_sched = 'schedule' + str(plant_id)
            identifier_data = 'data' + str(plant_id)
            for job in cron:
                if job.comment == identifier_sched or job.comment == identifier_data:
                    cron.remove(job)
                    cron.write()
        
        if plant_id:
            cur.execute("DELETE FROM plants WHERE id == ?", [plant_id])
            cur.execute(
                "DELETE FROM watering_days WHERE plant_id = ?", [plant_id])
            con.commit()
            con.close()
            return redirect("/adding_page")
        if plant_id_info:
            cur.execute("DELETE FROM plants WHERE id == ?", [plant_id_info])
            cur.execute("DELETE FROM watering_days WHERE plant_id = ?", [
                        plant_id_info])
            con.commit()
            con.close()
            return redirect("/")

    # User reached route via GET (as by submitting a form via GET)
    elif session["name"] != "flo":
        flash("No permissions to delete plants.")
        return redirect("/")
    else:
        return redirect("/")



# Water plant manually with button click
@app.route("/water_plant", methods=["GET", "POST"])
def waterPlant():
    pump_off()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST" and session["name"] == "flo":
        try:
            # Set GPIO(port) on LOW to water plant
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(port, GPIO.OUT)
            GPIO.output(port, 0)
            time.sleep(6)
        except Exception as e:
            print("Fail in water_plant: ", e)
            pump_off()
        finally:
            pump_off()
        return redirect("/")
    # User reached route via GET (as by submitting a form via GET)
    elif session["name"] != "flo":
        flash("No permissions to water plants.")
        return redirect("/")
    else:
        return redirect("/")


"""
COMING SOON:

@app.route("/update_watering_schedule", methods=["GET", "POST"])
def updateWateringSchedule():
    pump_off()

    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()
    plant_id = request.form.get("plant_id_schedupd")

    selected_days = []
    # Iterate through weekday selector data and write data into list
    for day in range(1, 8):
        form_field = 'dow' + str(day)
        print(form_field)
        print(request.form)
        if form_field in request.form:
            print(request.form.get(form_field))
            # Formatting the string in the right crontab-form
            selected_days.append(str(request.form.get(form_field)))
            
    if request.method == "POST":
        cur.execute("UPDATE plants SET watering_schedule = ? WHERE user_id == ? AND id == ?",
                    [selected_days, session["id"], plant_id])
        con.commit()
        con.close()
        # Write in Crontab File on Pi
        cron = CronTab(user='flopi')
        job = cron.new(command='python3 /home/flopi/Watering/Watering_app/sprinkle.py')
        job.dow.on(selected_days)
        job.hour.on(10) 
        cron.write()
        return redirect("/")
    else:
        return redirect("/")
"""


@app.route("/update_plant", methods=["GET", "POST"])
def update_plant():
    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Collecting form data
        # Necessary to only update the infos of plant which is selected
        plant_id = request.form.get("plant_id_upd")

        # Update plant data
        humidity = sensor_info()
        cur.execute("UPDATE plants SET humidity = ? WHERE user_id == ? AND id == ?", [
                    humidity, session["id"], plant_id])
        con.commit()
        cur.close()
        return redirect("/adding_page")
    # User reached route via GET (as by submitting a form via GET)
    else:
        return redirect("/adding_page")

# float_switch-Thread starten
floatswitch_thread = Thread(target=float_switch).start()
print("floatswitch_thread gestartet")

# Register the signal handler for SIGINT (CTRL+C)
signal.signal(signal.SIGINT, clean_exit)


if __name__ == "__main__":
    try:
        start_flask()

    except Exception as e:
        print("Fehler: ", e)


# plant_id_upd : input Refresh button for whole values of plant
# plant_id_schedup : input for changing watering_schedule
# plant_id : input for delete button


