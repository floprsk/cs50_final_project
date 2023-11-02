# dragonTree 
## Watering App on Raspberry Pi built with Flask
### Video Demo
https://www.youtube.com/watch?v=_ueGUjtDaRI
### Quick Desription:
With this Flask application, running on the Raspberry Pi (RPi), i can water my plant remotely and can add schedules, that it gets watered automatically. Also the humidity of the plantbed is displayed on the page and the humidity-data is logged regularly in a database on the RPi to display it later in Excel formats. It is also possible to add more than one plant alongside register & login functionality to scale it up later for more users. 

For now it works properly for me and for one plant. Adding more plants and users depends on the installation of the appropriate components (waterpumps, sensors, relays...) 

### Design
I tried to keep the design minimalistic and modern. 

![](https://github.com/floprsk/project/Watering_Design.gif)

![](https://github.com/floprsk/project/Watering_reg.gif)

![](https://github.com/floprsk/project/Watering_Mobile.gif)




The weekday picker is implemented with a for loop which loops through all possible inputs, which work kind of like html checkboxes. If a letter is clicked it is handed to the *request.form* element.

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
        
        >>>: Intendation 


### Technologies used:
- *Flask*

    Python webframework to create dynamic web-applications combined with pyhton code to controle hardware or something else.
    Leverages *Jinja2* to communicate bewteen html contents and pyhton code. When you run a flask project you can acces the application via an IP-Adress and handle user HTTP-requests.

- *Sqlite*

    Slim python database library used in the project to store the data of the users on a database on the RPi. If you need more power/functionality, then normal *SQL* is probably the way to go alongside *SQLAlchemy* python library.  

- *HTML, CSS, Javascript*

    With Flask you can easily build your applications with these 3 technologies, with the html-template functionalitys.


### Hardware & Components:

Watering Kit: https://tinyurl.com/ysztek5f

Raspberry Pi Zero 2 W: https://tinyurl.com/yvxapgye

AD Converter (MCP3008): https://tinyurl.com/yu66hjb8

Float Switch: https://tinyurl.com/yn6r9lkn

Power Supply and Cables: https://tinyurl.com/ym2k55nk

Power Adapter for Power Supply: https://tinyurl.com/ynamdxja


## Description of the Project:
The application with the database runs on the Raspberry Pi Zero 2 W. I used the service of Pitunnel.com to acces the application from the web, because i live in a student accomondation with special Wifi-restrictions. 
### app.py
This file is the centerpiece of the application, because it handles user interactions and requests.

In the several @routes, the inputs of the user via html forms (*templates* folder) are handled. Based on that, sqlite database operations are executed. These informations are passed to the html templates, where it also gets displayed for the user on the page. 

#### Functions related to the Raspberry Pi:

*def sensor_info()*:

Reads out humidity-sensor data and returns the value in percent. Has to be configured to the several sensor which depends on setup (resistants of cables etc...)

*def float_switch()*: 

This function runs threaded beneath the main  application and checks every 5 seconds if the water tank has got enough water. If not the waterpump is turned off. Otherwise the waterpump would get damaged over time, if it runs dry.

*def pump_off()*:

Turns waterpump off. GPIO Pin 12 in my case is set to HIGH (1) to switch off the relay which controls the waterpump.

#### Database functionality
The database is stored on the RPi. It contains four tables: 

(See also *create_db.txt*)
- users
    - id as Primary Key.
    - stores username 
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

    --> data log of humidity (Excel compatible)


The following Code has to be at the beginning of every route which handles database operations, to create the necessary database objects. Otherwise you will get an error: 

```
    # Connect with database
    con = sqlite3.connect("watering_users.db")
    cur = con.cursor()
```
#### Specifications:
    
Theres an explicit *watering_days* table because of Jinja2 problems i had with interpreting lists. 

When handing the *selected_days*[] list to an html template like that
- ['Mon', 'Tue', 'Fri']

every char was interpreted as an list element and not each day as one element. So every weekday column stores either *Nothing* or *1*, so that it can be displayed on the info_plant.html template.

Iteration through every element in the plants table:
(in *info_plant.html*)

    # Jinja2 notation 
    {% for plant in plants %}

Check if theres an entry for each day in the watering_days table (here as variable *days*) for this plant:

- plant[9]: number/count of the plant of the respective user
- plant[9]-1: Accesses the corresponding plant_id, which is the same as the plant_id in the *watering_days* table
- days[plant[9]-1]: Accesses weekday list of the respective plant


-> With that it is possible to display the several plants of the respective user which is logged in.

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
Need to have that to display only the elements of the current logged in user and also only manipulating the respective database entries.


#### Crontab functionality:
The cron daemon is used for the time-based execution of processes in Unix and Unix-like operating systems such as Linux, BSD or macOS in order to automate recurring tasks - cron jobs.

With the crontab library installed, you can edit the crontab file on your RPi with python. 
To use crontab-functionalites in python you will have to call a cron object like that at the beginning of every @app.route:
    
    cron = CronTab(user='flopi')


With "*comment = ...*" in the following line you can give every cron-job a name, with which you can identify which cron-job belongs to which plant.


    identifier_sched = 'schedule' + str(plant_id)
    job1 = cron.new(command='python3 /home/flopi/Watering/Watering_app/sprinkle.py', comment = identifier_sched )
    job1.dow.on(*selected_days)
    job1.hour.on(watering_time)

    cron.write()

You can also iterate through cron-jobs with the created cron-object and edit explicit crontab-lines.

    # Iterate through cron jobs and delete if theres already a schedule
    for job in cron:
        if job.comment == identifier_sched:
            cron.remove(job)
            cron.write()


#### Water the plant per button click
In the /water_plant @app.route the action is handled, when the user wants to water the plant manually.

    # Library to acces GPIO Pins on the RPi
    import RPi.GPIO as GPIO
    
    port = 12
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(port, GPIO.OUT)
    GPIO.output(port, 0)
    time.sleep(6)

You have to set the variable *port* to the GPIO Port on the Pi which is controlling the relay. Then you set it up as output and set it either 0 or 1, based on the relay you got. The time.sleep(seconds) function controles how long the waterpump is active.


### HTML templates
Several times in *app.py* the function

    render_template("file.html", placeholder = element)

is called. 

With that method you can display html files for the user on the Web-Application. 

**All the templates have to be in the same directory as the app.py file as a folder called "templates"!**

The *layout.html* file is the base of all html templates for me. 

With adding

    # Jinja2 notation   
    {% extends "layout.html" %} 

at the top of your other html-templates you dont have to add the code for redundant elements like a nav on every template. But look in the files to see how it is exaclty done. 

### Jinja 2
Template engine which is already included with the installation of Flask. 

All the "{%%}" and "{{}}" notations in the html template codes refer to Jinja2.

    element = ['Mon', 'Tue', 'Fri']
    render_template("file.html", placeholder = element)

In the *app.py* code it is also used here: 

- placeholder = element

With that notation you can hand elements to an html template and display it there and even iterate through it with loops. In  the html template you can iterate through the element like that:

    {% for day in placeholder %}
        ...
    {% endfor %}

You can call it wathever you want, but it works like the principle of an placeholder, so i called it like that.


### Infos on Usage:
To work properly and to see all functionalities of the application, you will need to connect the necessary Hardware in real life, but you can watch my Video Demo to get more information about that.
### Want to test a Demo Version on your own system?
*python has to be installed on your system*
- Create a directory (call it *app* or something) on your system with the **app_pc.py** file and the *templates* folder as a seperate! folder in the *app* folder  
- Download the **watering_users.db** file and put it also in the *app*-directory
    - You can also create the sqlite3-database on your own (commands documented in **create_db.txt**)
- Install the necessary librarys on your system, documented in **requirements.txt** (command: pip3 install "library")
- Open a command prompt in the *app*-directory and execute **_flask run_**, then you can acces the demo-app on your localhost
- (The register functionality will just store the data on your own system in the watering_users.db file, so no worrys)
