import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "https://faceattendancerealtime-fb9f2-default-rtdb.firebaseio.com/"
})


ref = db.reference('Students')

data = {
    "100000":
        {
            "name": "Amith H D",
            "major": "CSE",
            "starting_year": 2020,
            "total_attendance": 0,
            "standing": "G",
            "year": 4,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "100001":
        {
            "name": "Emly Blunt",
            "major": "Economics",
            "starting_year": 2021,
            "total_attendance": 0,
            "standing": "B",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "100002":
        {
            "name": "Elon Musk",
            "major": "Science",
            "starting_year": 2020,
            "total_attendance": 0,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "100003":
        {
            "name": "Anand",
            "major": "Physics",
            "starting_year": 2020,
            "total_attendance": 0,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "100004":
        {
            "name": "Sujal",
            "major": "Student",
            "starting_year": 2020,
            "total_attendance": 0,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "100005":
        {
            "name": "Sakshi",
            "major": "Student",
            "starting_year": 2022,
            "total_attendance": 0,
            "standing": "G",
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
}

for key, value in data.items():
    ref.child(key).set(value)