import mysql.connector
from mysql.connector import Error
from flask import Flask, request, render_template, redirect

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def renderLoginPage():
    events = runQuery("SELECT * FROM events")
    branch = runQuery("SELECT * FROM branch")
    if request.method == 'POST':
        Name = request.form['FirstName'] + " " + request.form['LastName']
        Mobile = request.form['MobileNumber']
        Branch_id = request.form['Branch']
        Event = request.form['Event']
        Email = request.form['Email']

        if len(Mobile) != 10:
            return render_template('loginfail.html', errors=["Invalid Mobile Number!"])

        if not Email.endswith('.com'):
            return render_template('loginfail.html', errors=["Invalid Email!"])

        existing_participant = runQuery("SELECT * FROM participants WHERE event_id=%s AND mobile=%s", (Event, Mobile))
        if existing_participant:
            return render_template('loginfail.html', errors=["Student already Registered for the Event!"])

        participant_count = runQuery("SELECT COUNT(*) FROM participants WHERE event_id=%s", (Event,))[0][0]
        max_participants = runQuery("SELECT participants FROM events WHERE event_id=%s", (Event,))[0][0]
        if participant_count >= max_participants:
            return render_template('loginfail.html', errors=["Participants count fulfilled Already!"])

        runQuery("INSERT INTO participants(event_id, fullname, email, mobile, college, branch_id) VALUES(%s, %s, %s, %s, %s, %s)", 
                 (Event, Name, Email, Mobile, "COEP", Branch_id))

        return render_template('index.html', events=events, branchs=branch, errors=["Successfully Registered!"])

    return render_template('index.html', events=events, branchs=branch)

@app.route('/loginfail', methods=['GET'])
def renderLoginFail():
    return render_template('loginfail.html')

@app.route('/admin', methods=['GET', 'POST'])
def renderAdmin():
    if request.method == 'POST':
        UN = request.form['username']
        PS = request.form['password']

        cred = runQuery("SELECT * FROM admin")
        for user in cred:
            if UN == user[0] and PS == user[1]:
                return redirect('/eventType')

        return render_template('admin.html', errors=["Wrong Username/Password"])

    return render_template('admin.html')

@app.route('/eventType', methods=['GET', 'POST'])
def getEvents():
    eventTypes = runQuery(
        "SELECT *,(SELECT COUNT(*) FROM participants AS P WHERE T.type_id IN (SELECT type_id FROM events AS E WHERE E.event_id = P.event_id)) AS COUNT FROM event_type AS T"
    )
    events = runQuery(
        "SELECT event_id, event_title, (SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id) AS count FROM events AS E"
    )
    types = runQuery("SELECT * FROM event_type")
    location = runQuery("SELECT * FROM location")

    if request.method == "POST":
        try:
            Name = request.form["newEvent"]
            fee = request.form["Fee"]
            participants = request.form["maxP"]
            Type = request.form["EventType"]
            Location = request.form["EventLocation"]
            Date = request.form['Date']
            runQuery(
                "INSERT INTO events(event_title, event_price, participants, type_id, location_id, date) VALUES(%s, %s, %s, %s, %s, %s)", 
                (Name, fee, participants, Type, Location, Date)
            )

        except Exception as e:
            print("Error inserting or deleting event:", e)
            EventId = request.form.get("EventId")
            if EventId:
                runQuery("DELETE FROM events WHERE event_id=%s", (EventId,))

    return render_template('events.html', events=events, eventTypes=eventTypes, types=types, locations=location)

@app.route('/eventinfo')
def rendereventinfo():
    events = runQuery(
        "SELECT *,(SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id) AS count FROM events AS E LEFT JOIN event_type USING(type_id) LEFT JOIN location USING(location_id)"
    )
    return render_template('events_info.html', events=events)

@app.route('/participants', methods=['GET', 'POST'])
def renderParticipants():
    events = runQuery("SELECT * FROM events")

    if request.method == "POST":
        Event = request.form['Event']
        participants = runQuery("SELECT p_id, fullname, mobile, email FROM participants WHERE event_id=%s", (Event,))
        return render_template('participants.html', events=events, participants=participants)

    return render_template('participants.html', events=events)

def runQuery(query, params=None):
    db = None
    try:
        # Initialize the connection
        db = mysql.connector.connect(
            host='localhost',
            database='event_mgmt',
            user='root',
            password='kalpana123'
        )

        if db.is_connected():
            print("Connected to MySQL, running query: ", query)
            cursor = db.cursor(buffered=True)
            cursor.execute(query, params)
            db.commit()

            # Try to fetch results if the query is expected to return data
            try:
                res = cursor.fetchall()
            except Exception as e:
                print("Query returned nothing, ", e)
                return []
            return res

    except Error as e:
        print("Error:", e)
        return []

    finally:
        if db and db.is_connected():
            db.close()

if __name__ == "__main__":
    app.run(debug=True)