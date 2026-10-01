from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'super-secret-key'

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# ================= Helper Functions =================
def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump([], f)
    with open(path, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# ================= LOGIN & LOGOUT =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # ADMIN LOGIN
        for a in load_json('admins.json'):
            if a['username'] == username and a['password'] == password:
                session['username'] = username
                session['role'] = 'Admin'
                return redirect(url_for('dashboard'))

        # STUDENT LOGIN
        for s in load_json('students.json'):
            if s.get('username') == username and s.get('password') == password:
                session['username'] = username
                session['role'] = 'Student'
                return redirect(url_for('student_profile'))

        return render_template('login.html', error="Invalid ID or Password")

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ================= DASHBOARD =================
@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'username' not in session or session.get('role')!='Admin':
        return redirect(url_for('login'))
    return render_template('Dashboard.html', user=session['username'], role='Admin')

# ================= STUDENT PROFILE =================
@app.route('/student_profile')
def student_profile():
    if 'username' not in session or session.get('role')!='Student':
        return redirect(url_for('login'))

    username = session['username']
    students = load_json('students.json')
    student = next((s for s in students if s.get('username')==username), None)
    if not student:
        return "Student record not found"

    reg_no = student.get('reg_no')

    # Fetch related records safely (convert reg_no to str for consistency)
    student['guardian'] = next((g for g in load_json('guardian.json') if str(g.get('reg_no'))==str(reg_no)), {})
    student['hostel'] = next((h for h in load_json('hostel.json') if str(h.get('reg_no'))==str(reg_no)), {})
    student['attendance'] = next((a for a in load_json('attendance.json') if str(a.get('reg_no'))==str(reg_no)), {})
    student['billing'] = next((b for b in load_json('billing.json') if str(b.get('reg_no'))==str(reg_no)), {})
    student['mess'] = next((m for m in load_json('mess.json') if str(m.get('reg_no'))==str(reg_no)), {})
    student['checkinout'] = next((c for c in load_json('checkinout.json') if str(c.get('reg_no'))==str(reg_no)), {})
    student['dues'] = [d for d in load_json('dues.json') if str(d.get('reg_no'))==str(reg_no)]
    student['fees'] = next((f for f in load_json('fees.json') if str(f.get('reg_no'))==str(reg_no)), {})

    return render_template('student_profile.html', student=student)


# ================= STUDENT CRUD =================
@app.route('/student_info')
def student_info():
    if 'username' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))

    students = load_json('students.json')
    guardians = load_json('guardian.json')
    hostels = load_json('hostel.json')

    for s in students:
        reg_no = s['reg_no']
        s['guardian'] = next((g for g in guardians if g['reg_no'] == reg_no), {})
        s['hostel'] = next((h for h in hostels if h['reg_no'] == reg_no), {})

    return render_template('student_info.html', students=students)

@app.route('/register_student', methods=['GET'])
def register_student_page():
    if 'username' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    return render_template('register_student.html')

@app.route('/register_student', methods=['POST'])
def register_student():
    if 'username' not in session or session.get('role') != 'Admin':
        return jsonify(success=False, message="Unauthorized")

    try:
        data = request.get_json()
        students = load_json('students.json')

        # Prevent duplicate Reg No or Username
        if any(s['reg_no'] == data['reg_no'] or s['username'] == data['username'] for s in students):
            return jsonify(success=False, message="Duplicate Reg No or Username")

        student = {
            "reg_no": data['reg_no'],
            "full_name": data['full_name'],
            "username": data['username'],
            "password": data['password'],
            "gender": data['gender'],
            "dob": data['dob'],
            "contact": data['contact'],
            "address": data['address'],
            "role": "Student"
        }

        students.append(student)
        save_json('students.json', students)

        reg_no = data['reg_no']

        auto_files = [
            ('guardian.json', {
                "reg_no": reg_no,
                "name": data['guardian']['name'],
                "contact": data['guardian']['contact']
            }),
            ('hostel.json', {
                "reg_no": reg_no,
                "floor_no": data.get('hostel', {}).get('floor_no', ''),
                "room_no": data.get('hostel', {}).get('room_no', '')
            }),
            ('attendance.json', {
                "reg_no": reg_no,
                "status": "Absent",
                "check_in_date": "",
                "check_in_time": "",
                "check_out_date": "",
                "check_out_time": ""
            }),
            ('billing.json', {
                "reg_no": reg_no,
                "mess_bill": 0,
                "mess_status": "Unpaid",
                "hostel_dues": 0,
                "dues_status": "Unpaid",
                "payable_fund": 0,
                "fund_status": "Unpaid"
            }),
            ('mess.json', {
                "reg_no": reg_no,
                "month1": 0,
                "month2": 0,
                "month3": 0,
                "status1": "Unpaid",
                "status2": "Unpaid",
                "status3": "Unpaid"
            }),
            ('checkinout.json', {
                "reg_no": reg_no,
                "check_in": "",
                "check_out": "",
                "status": "Out"
            }),
            ('dues.json', {
                "payment_id": "",
                "reg_no": reg_no,
                "amount": 0,
                "status": "Unpaid",
                "date": ""
            }),
            ('fees.json', {
                "id": "",
                "reg_no": reg_no,
                "fine_amount": 0,
                "fine_status": "Unpaid",
                "fund_amount": 0,
                "fund_status": "Unpaid",
                "remaining_dues": 0
            })
        ]

        for filename, record in auto_files:
            lst = load_json(filename)
            lst.append(record)
            save_json(filename, lst)

        # 🔹 Update room occupancy if a room is assigned
        room_no = data.get('hostel', {}).get('room_no')
        if room_no:
            rooms = load_json('rooms.json')
            for r in rooms:
                if str(r['room_no']) == str(room_no):
                    r['occupied'] = 1
                    save_json('rooms.json', rooms)
                    break

        return jsonify(success=True)

    except Exception as e:
        print("REGISTER ERROR:", e)
        return jsonify(success=False, message="Server error")

@app.route('/update_student', methods=['POST'])
def update_student():
    if 'role' not in session or session['role']!='Admin':
        return jsonify(success=False, message='Unauthorized')

    updated = request.get_json()
    students = load_json('students.json')
    for s in students:
        if s['reg_no'] == updated.get('reg_no'):
            s.update(updated)
            save_json('students.json', students)
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/delete_student/<reg_no>', methods=['POST'])
def delete_student(reg_no):
    if 'role' not in session or session['role']!='Admin':
        return jsonify(success=False, message='Unauthorized')

    # 🔹 Free the assigned room when student is deleted
    hostel_data = load_json('hostel.json')
    room_no = next((h.get('room_no') for h in hostel_data if h.get('reg_no')==reg_no), None)
    if room_no:
        rooms = load_json('rooms.json')
        for r in rooms:
            if str(r['room_no'])==str(room_no):
                r['occupied'] = 0
        save_json('rooms.json', rooms)

    for fname in ['students.json','guardian.json','hostel.json','attendance.json','billing.json','mess.json']:
        data = load_json(fname)
        data = [d for d in data if d.get('reg_no') != reg_no]
        save_json(fname, data)

    return jsonify(success=True)

# ================= ATTENDANCE CRUD =================
@app.route('/attendance')
def attendance():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('Attendance.html', attendance=load_json('attendance.json'))

@app.route('/save_attendance', methods=['POST'])
def save_attendance():
    data = request.get_json()
    attendance = load_json('attendance.json')

    existing = next((a for a in attendance if a.get('id')==data.get('id')), None)
    if existing:
        existing.update(data)
    else:
        data['id'] = max([a.get('id',0) for a in attendance]+[0])+1
        attendance.append(data)

    save_json('attendance.json', attendance)
    return jsonify(success=True)

@app.route('/delete_attendance/<int:att_id>', methods=['POST'])
def delete_attendance(att_id):
    attendance = load_json('attendance.json')
    attendance = [a for a in attendance if a.get('id') != att_id]
    save_json('attendance.json', attendance)
    return jsonify(success=True)

# ================= CHECK-IN/OUT CRUD =================
@app.route('/checkin')
def checkin():
    return render_template('check_inandout.html', checkinout=load_json('checkinout.json'))

@app.route('/add_checkinout', methods=['POST'])
def add_checkinout():
    data = request.get_json()
    checkinout = load_json('checkinout.json')
    if any(r['reg_no']==data['reg_no'] for r in checkinout):
        return jsonify(success=False, message='Record exists')
    checkinout.append(data)
    save_json('checkinout.json', checkinout)
    return jsonify(success=True)

@app.route('/update_checkinout', methods=['POST'])
def update_checkinout():
    data = request.get_json()
    checkinout = load_json('checkinout.json')
    for r in checkinout:
        if r['reg_no']==data['reg_no']:
            r.update(data)
            save_json('checkinout.json', checkinout)
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/remove_checkinout', methods=['POST'])
def remove_checkinout():
    data = request.get_json()
    checkinout = load_json('checkinout.json')
    checkinout = [r for r in checkinout if r['reg_no']!=data['reg_no']]
    save_json('checkinout.json', checkinout)
    return jsonify(success=True)

# ================= DUES CRUD =================
@app.route('/dues')
def dues():
    return render_template('Dues.html', dues=load_json('dues.json'))

@app.route('/save_dues', methods=['POST'])
def save_dues():
    data = request.get_json()
    dues = load_json('dues.json')
    if data.get('payment_id'):
        for d in dues:
            if d['payment_id']==data['payment_id']:
                d.update(data)
                save_json('dues.json', dues)
                return jsonify(success=True)
        return jsonify(success=False)
    else:
        data['payment_id'] = str(max([int(d.get('payment_id',0)) for d in dues]+[0])+1)
        dues.append(data)
        save_json('dues.json', dues)
        return jsonify(success=True, payment_id=data['payment_id'])

@app.route('/delete_dues/<payment_id>', methods=['POST'])
def delete_dues(payment_id):
    dues = load_json('dues.json')
    dues = [d for d in dues if d['payment_id']!=payment_id]
    save_json('dues.json', dues)
    return jsonify(success=True)


# ================= FINE & FUNDS CRUD =================
@app.route('/fund')
def fund():
    return render_template('Fineandfunds.html', fees_data=load_json('fees.json'))

@app.route('/add_fee_record', methods=['POST'])
def add_fee_record():
    data = request.get_json()
    fees = load_json('fees.json')
    data['id'] = str(max([int(f.get('id',0)) for f in fees]+[0])+1)
    data['fine_status'] = 'Unpaid'
    data['fund_status'] = 'Unpaid'
    data['remaining_dues'] = int(data.get('fine_amount',0))+int(data.get('fund_amount',0))
    fees.append(data)
    save_json('fees.json', fees)
    return jsonify(success=True, id=data['id'])

@app.route('/toggle_fine_status', methods=['POST'])
def toggle_fine_status():
    data = request.get_json()
    fees = load_json('fees.json')
    for f in fees:
        if f['id']==data['id']:
            f['fine_status'] = 'Paid' if f['fine_status']=='Unpaid' else 'Unpaid'
            f['remaining_dues'] = (0 if f['fine_status']=='Paid' else f['fine_amount']) + \
                                   (0 if f['fund_status']=='Paid' else f['fund_amount'])
            save_json('fees.json', fees)
            return jsonify(success=True, new_status=f['fine_status'])
    return jsonify(success=False)

@app.route('/toggle_fund_status', methods=['POST'])
def toggle_fund_status():
    data = request.get_json()
    fees = load_json('fees.json')
    for f in fees:
        if f['id']==data['id']:
            f['fund_status'] = 'Paid' if f['fund_status']=='Unpaid' else 'Unpaid'
            f['remaining_dues'] = (0 if f['fine_status']=='Paid' else f['fine_amount']) + \
                                   (0 if f['fund_status']=='Paid' else f['fund_amount'])
            save_json('fees.json', fees)
            return jsonify(success=True, new_status=f['fund_status'])
    return jsonify(success=False)

@app.route('/remove_fee_record', methods=['POST'])
def remove_fee_record():
    data = request.get_json()
    fees = load_json('fees.json')
    fees = [f for f in fees if f['id']!=data['id']]
    save_json('fees.json', fees)
    return jsonify(success=True)

# ================= MESS CRUD =================
@app.route('/mess')
def mess():
    return render_template('mess.html', mess=load_json('mess.json'))

@app.route('/add_mess', methods=['POST'])
def add_mess():
    data = request.get_json()
    mess = load_json('mess.json')
    if any(m['reg_no']==data['reg_no'] for m in mess):
        return jsonify(success=False, message='Record exists')
    data.update({'status1':'Unpaid','status2':'Unpaid','status3':'Unpaid'})
    mess.append(data)
    save_json('mess.json', mess)
    return jsonify(success=True)

@app.route('/update_mess', methods=['POST'])
def update_mess():
    data = request.get_json()
    reg_no = data['reg_no']
    mess = load_json('mess.json')
    for m in mess:
        if m['reg_no']==reg_no:
            m.update(data)
            save_json('mess.json', mess)
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/remove_mess', methods=['POST'])
def remove_mess():
    data = request.get_json()
    reg_no = data['reg_no']
    mess = load_json('mess.json')
    mess = [m for m in mess if m['reg_no']!=reg_no]
    save_json('mess.json', mess)
    return jsonify(success=True)

# ================= FLOORS & ROOMS =================
@app.route('/floors')
def floors():
    return render_template('floors.html', floors=load_json('floors.json'))

@app.route('/add_floor', methods=['POST'])
def add_floor():
    data = request.get_json()
    floors = load_json('floors.json')
    if any(str(f['floor_no'])==str(data['floor_no']) for f in floors):
        return jsonify(success=False, message='Floor exists')
    floors.append({
        'floor_no': str(data['floor_no']),
        'total_rooms': int(data.get('total_rooms',0)),
        'occupied_rooms': int(data.get('occupied_rooms',0))
    })
    save_json('floors.json', floors)
    return jsonify(success=True)

@app.route('/update_floor', methods=['POST'])
def update_floor():
    data = request.get_json()
    floors = load_json('floors.json')
    for f in floors:
        if str(f['floor_no'])==str(data['floor_no']):
            f['total_rooms']=int(data.get('total_rooms',f['total_rooms']))
            f['occupied_rooms']=int(data.get('occupied_rooms',f['occupied_rooms']))
            save_json('floors.json', floors)
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/remove_floor', methods=['POST'])
def remove_floor():
    data = request.get_json()
    floors = load_json('floors.json')
    floors = [f for f in floors if str(f['floor_no'])!=str(data['floor_no'])]
    save_json('floors.json', floors)
    return jsonify(success=True)

@app.route('/rooms')
def rooms():
    return render_template('rooms.html', rooms=load_json('rooms.json'))

@app.route('/add_room', methods=['POST'])
def add_room():
    data = request.get_json()
    rooms = load_json('rooms.json')
    if any(str(r['room_no'])==str(data['room_no']) for r in rooms):
        return jsonify(success=False, message='Room exists')
    rooms.append({
        'room_no': str(data['room_no']),
        'floor_no': str(data.get('floor_no','')),
        'capacity': int(data.get('capacity',0)),
        'occupied': int(data.get('occupied',0))
    })
    save_json('rooms.json', rooms)
    return jsonify(success=True)

@app.route('/update_room', methods=['POST'])
def update_room():
    if 'role' not in session or session['role'] != 'Admin':
        return jsonify(success=False, message='Unauthorized')

    data = request.get_json()
    room_no = data.get('room_no')
    floors = data.get('floor_no')
    capacity = data.get('capacity')
    occupied = data.get('occupied')

    rooms = load_json('rooms.json')
    for r in rooms:
        if str(r['room_no']) == str(room_no):
            if floors is not None:
                r['floor_no'] = floors
            if capacity is not None:
                r['capacity'] = int(capacity)
            if occupied is not None:
                r['occupied'] = int(occupied)
            save_json('rooms.json', rooms)
            return jsonify(success=True)

    return jsonify(success=False, message='Room not found')

@app.route('/remove_room', methods=['POST'])
def remove_room():
    data = request.get_json()
    rooms = load_json('rooms.json')
    rooms = [r for r in rooms if str(r['room_no'])!=str(data['room_no'])]
    save_json('rooms.json', rooms)
    return jsonify(success=True)

@app.route('/about')
def about():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('about.html')

# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)
