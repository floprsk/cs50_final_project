# dragonTree 
## Watering App on Raspberry Pi built with Flask
### Video Demo
https://www.youtube.com/watch?v=_ueGUjtDaRI
### Quick Description:
With this Flask application, running on the Raspberry Pi (RPi), i can water my plant remotely and can add schedules, that it gets watered automatically. Also the humidity of the plant bed is displayed on the page and the humidity-data is logged regularly in a database on the RPi to display it later in Excel formats. It is also possible to add more than one plant alongside register & login functionality to scale it up later for more users. 

For now it works properly for me and for one plant. Adding more plants and users depends on the installation of the appropriate components (waterpumps, sensors, relays...) 


### Technologies used:
- *Flask*

    Python web framework to create dynamic web-applications combined with Python code to control hardware or something else.
    Leverages *Jinja2* to communicate between HTML contents and Python code. When you run a flask project you can access the application via an IP and handle user HTTP-requests.

- *Sqlite*

    Slim Python database library used in the project to store the data of the users on a database on the RPi. If you need more power/functionality, then normal *SQL* is probably the way to go alongside *SQLAlchemy* Python library.  

- *HTML, CSS, Javascript*

    With Flask you can easily build your applications with these 3 technologies, with the HTML-template functionalities.


### Design
#### Mobile View

![](https://github.com/floprsk/project/blob/main/Watering_Mobile.gif)

#### Desktop View
![](https://github.com/floprsk/project/blob/main/Watering_Design.gif)  

The weekday picker is implemented with a for loop which loops through all possible inputs, which work kind of like HTML checkboxes. If a letter is clicked it is handed to the *request.form* element.

    # Flask (app.py) Code
    selected_days = []

    # Iterate through weekday selector data and write data into list

    for day in range(1, 8):

    # weekday selector is build with explicit input names to detect the days which are selected
    # value of these inputs are 'Mon', 'Tue', 'Wed...

        form_field = 'dow' + str(day)
        if form_field in request.form:
    >>>>selected_days.append(request.form.get(form_field))
        # Formatting selected_days in the right   
        # crontab-form
        # Example: ['Mon', 'Thu', 'Sun']
        
        >>>: Indentation 

#### Register functionality
Ensured, that the user inputs the forms correctly, also when logging in, the password is checked etc.

![](https://github.com/floprsk/project/blob/main/Watering_reg.gif)



## Description of the Project:
The application with the database runs on the Raspberry Pi Zero 2 W. I used the service of Pitunnel.com to access the application from the web, because i live in a student accommodation with special Wifi-restrictions. 
### app.py
This file is the centerpiece of the application, because it handles user interactions and requests.

In the several @routes, the inputs of the user via HTML forms (*templates* folder) are handled. Based on that, sqlite database operations are executed. These information is passed to the HTML templates, where it also gets displayed for the user on the page. 

#### Functions related to the Raspberry Pi:

*def sensor_info()*:

Reads out humidity-sensor data by reading out the corresponding SPI port and returns the value in percent. Has to be configured to the several sensor which depends on setup (resistances of cables etc...)

*def float_switch()*: 

This function runs threaded beneath the main  application and checks every 5 seconds if the water tank has got enough water. If not the water pump is turned off. Otherwise the water pump would get damaged over time, if it runs dry.

*def pump_off()*:

Turns water pump off. GPIO Pin 12 in my case is set to HIGH (1) to switch off the relay which controls the water pump.

#### Database functionalities
The database is stored on the RPi. It contains four tables: 

(See also *create_db.txt*)
- users
    - id as Primary Key.
    - username 
    - hashed password
- plants
    - id as Primary Key
    - all the information about the plant 
    - user_id as Foreign Key referring to users(id)
    - number/count of plants of the respective user
- watering_days
    - plant id as Primary & Foreign Key referring to plants(id)
    - every weekday as column
- data
    - id as Primary Key
    - timestamp and humidity in percent

    --> works properly for the setup with one plant, to add the functionality for more plants, you would have to add a several column with refers to the respective plant id's of the plants

The following Code has to be at the beginning of every route which handles database operations, to create the necessary database objects. Otherwise you will get an error: 

```
    # Connect with database
    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()
```

You can manipulate your database like that: 

    cur.execute("DELETE FROM watering_days WHERE plant_id = ?", [plant_id])
    con.commit()
    con.close()

The "?" notation is used to prevent SQL-Injection-Attacks. With con.commit() you commit your database actions to the database and with con.close() you close the connection.

#### Specifications:
    
Theres an explicit *watering_days* table because of Jinja2 problems i had with interpreting lists. 

When handing the *selected_days*[] list to an HTML template like that
- ['Mon', 'Tue', 'Fri']

every char was interpreted as an list element and not each day as one element. So every column in the table *watering_days* stores either *Nothing* or *1*, so that it can be displayed on the info_plant.HTML template:

Iteration through every element in the plants table:
(in *info_plant.HTML*)

    # info_plant.HTML file
    # Jinja2 notation 
    {% for plant in plants %}

Check if theres an entry for each day in the watering_days table (here as variable *days*) for this plant:

- plant[9]: number/count of the plant of the respective user
- plant[9]-1: Accesses the corresponding plant_id, which is the same as the plant_id in the *watering_days* table
- days[plant[9]-1]: Accesses weekday list of the respective plant


-> With that it is possible to display the several plants of the respective user which is logged in.

    # info_plant.HTML file
    # Jinja2 notation 
    {% if days[plant[9]-1][2] %} <!--mon-->
        Mon
    {% endif %} 
    {% if days[plant[9]-1][3] %} <!--tue-->
        Tue
    {% endif %} 
    {% if days[plant[9]-1][4] %} <!--wed-->
        Wed
    {% endif %} 
    {% if days[plant[9]-1][5] %} <!--thi-->
        Thi
    {% endif %}                                 
    {% if days[plant[9]-1][6] %} <!--fri-->
        Fri
    {% endif %}
    {% if days[plant[9]-1][7] %} <!--sat-->
        Sat
    {% endif %}
    {% if days[plant[9]-1][8] %} <!--sun-->
        Sun
    {% endif %} 
    
    {% endfor %}



#### Session functionality:
Need to have that, to display only the elements of the current logged in user and also only manipulating the respective database entries.


#### Crontab functionality:
The cron daemon is used for the time-based execution of processes in Unix and Unix-like operating systems in order to automate recurring tasks, also called cron jobs. 

With the crontab library installed, you can edit the crontab file on your RPi with Python. 
To use crontab functionalities in Python you will have to call a cron object like that at the beginning of every @app.route:
    
    # app.py file
    cron = CronTab(user='username_on_Pi')


With "*comment = ...*" in the following line you can give every cron-job a name, with which you can identify which cron-job belongs to which plant.

    # app.py file
    identifier_sched = 'schedule' + str(plant_id)
    job1 = cron.new(command='Python3 /home/flopi/Watering/Watering_app/sprinkle.py', comment = identifier_sched )
    job1.dow.on(*selected_days)
    job1.hour.on(watering_time)

    cron.write()

The "*selected_days" is a nice Python tweak, which interprets the selected_days list (i. e. ['Mon', 'Tue', 'Fri']) list properly, in contrast to Jinja2, so that every day in the list is added to the crontab file in the right notation.

So i am storing the information about the watering days once in the table *plants* additionally, although i got an extra table *watering_days*. But it is not necessary to store the data two times, as the crontab commands do not depend on database operations but only on the variable *selected_days*. 

You can also iterate through cron-jobs with the created cron-object and edit explicit crontab-lines.

    # app.py file
    # Iterate through cron jobs and delete if theres already a schedule
    for job in cron:
        if job.comment == identifier_sched:
            cron.remove(job)
            cron.write()

Similar methods are used for the implementation of the data log cron jobs. 

It is also important to keep the right sequence of this part of the code, because some parts depend on the variables *selected_days* *plant_id* and *plant_number* which are declared after the plant was added to the table *plants*. 

#### Water the plant per button click
In the /water_plant @app.route the action is handled, when the user wants to water the plant manually per button click.

    # app.py file
    # Library to access GPIO Pins on the RPi
    import RPi.GPIO as GPIO
    
    port = 12
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(port, GPIO.OUT)
    GPIO.output(port, 0)
    time.sleep(6)


You have to declare the variable *port* as the GPIO Port on the Pi which is controlling the relay. Be aware of the two possible GPIO.setmode() options, BCM or BOARD. Then you set it up as output and set it either 0 or 1, based on the relay you got. The *time.sleep(seconds)* function control how long the water pump is active.


### HTML templates
Several times in *app.py* the function

    # app.py file
    render_template("file.HTML", placeholder = element)

is called. 

With that method you can display HTML files for the user on the Web-Application. It can be applied with familiar HTML and you can add also CSS and Javascript like you would do normally.

**All the templates have to be in the same directory as the app.py file as a folder called "templates"!**

The *layout.HTML* file is the base of all HTML templates for me. 

With adding

    # HTML template files  
    {% extends "layout.HTML" %} 

at the top of your other HTML-templates you do not have to add the code for redundant elements like a nav on every template. But look in the files to see how it is exactly done. 

### Jinja 2
Template engine which is already included with the installation of Flask. 

All the "{%%}" and "{{}}" notation in the HTML template codes refers to Jinja2. You can 

In the *app.py* code it is also used here: 

    # app.py file
    element = ['Mon', 'Tue', 'Fri']
    render_template("file.HTML", placeholder = element)

In the HTML-templates you can display the template for example like that:
```
    # HTML-template files
    <p>Here is the element: {{placeholder}}</p>
```
You can also use loops and other great functionalities in between the "{%%}" notation:

    # HTML-template files
    # create a div for every element in placeholder:
    {% for day in placeholder %}
        <div>
            {{ placeholder[day] }}
        </div>
    {% endfor %}

You can call it whatever you want, but it works like the principle of an placeholder, so i called it like that.

### Other files on the RPi:
- *boot.py*

    Is executed on every reboot because it is configured like that in the crontab-file manually:

        @reboot Python3 (path to boot.py file)

    Switches off the relay which controls the water pump on every boot of the system.

- *sprinkle.py*

    There was already an @app.route("/water_plant"...) to water the plant manually when the button is clicked. But to configure a schedule on the RPi with crontab for automatic watering i used an external file which is added to the crontab file as command like that:

        job1 = cron.new(command='.../sprinkle.py',  comment = identifier_sched )
        cron.write()

- *log_data.py*

    Connects to the *watering_users* database and reads out the humidity-sensor. Inserts the data alongside a timestamp into the table *data* in an format compatible with Excel. This functionality works for one plant properly but would also be possible to scale it up.



### Infos on Usage:
To work properly and to see all functionalities of the application, you will need to connect the necessary Hardware in real life, but you can watch my **Video Demo** to get more information about that.

### Hardware & Components:

Watering Kit: https://tinyurl.com/ysztek5f

Raspberry Pi Zero 2 W: https://tinyurl.com/yvxapgye

AD Converter (MCP3008): https://tinyurl.com/yu66hjb8

Float Switch: https://tinyurl.com/yn6r9lkn

Power Supply and Cables: https://tinyurl.com/ym2k55nk

Power Adapter for Power Supply: https://tinyurl.com/ynamdxja


### Want to test a Demo Version on your own system?
*Python has to be installed on your system*
- Create a directory (call it *app* or something) on your system with the **app_pc.py** file and the *templates* and *static* folder as separate! folders in the *app* folder  
- Download the **watering_users.db** file and put it also in the *app*-directory
    - You can also create the sqlite3-database on your own (commands documented in **create_db.txt**)
- Install the necessary libraries on your system, documented in **requirements.txt** (command: pip3 install "library")
- Open a command prompt in the *app*-directory and execute **_flask run_**, then you can access the demo-app on your localhost
- In the Demo Version (app_pc.py) the functions interacting with the RPi are commented out. 
- (The register functionality will just store the data on your own system in the watering_users.db file, so no worries)
