from django.shortcuts import render
from django.template import RequestContext, loader
from adminStaff.models import AdminStaff, AttendanceDaily
from portal.models import Course, Feedback, Notification
from django.http import HttpResponseRedirect
from Faculty.models import Faculty
from Students.models import Record, Marks, Student, SGPA
from django.db import connection
from django.http import HttpResponse
from Reports.views import *
from django.core.mail import send_mail
import csv
from portal.views import checkIdentity, search, portalSearchResults
from Students.views import studentViewStudentProfile
from django.db.models import Sum
from django.core.urlresolvers import reverse
from django.http import HttpResponse
#from django.http import HttpResponseRedirect

from adminStaff.forms import DocumentForm,read
import os,sys
import numpy as np 
from string import whitespace
import CSP.settings


def addNewMonthlyAttendance(request,course_code):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        if request.method == 'POST':   
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            classes_taken_place = request.POST['classes_taken_place']
            course = Course.objects.get(id= course_code)
            try:
                save = AttendanceMonthly.objects.create(start_date=start_date,end_date=end_date,classes_taken_place=classes_taken_place,coursecode=course)
                save.save()
            except:
                pass
        return courseHome(request,course_code)
    return HttpResponseRedirect(redirect)


def uploadSeatingChart(request,course_code):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        if request.method == 'POST':   
            date = request.POST['dateOfAttendance']
            chart = request.FILES['seating']
            seats = request.POST.getlist('SD[]')
            newdoc = Document(docfile = chart)
            newdoc.save()
            course = Course.objects.get(id= course_code)
            path = os.path.abspath(newdoc.docfile.url[1:])
            mark = np.genfromtxt(path, dtype='str', delimiter=',',unpack='True',skip_header=1)
            for i in range(250):
                try:
                    # k = mark[1][i]
                    student = Student.objects.get(rollno=int(mark[1][i]))
                    studentInCourse = course.getStudents().filter(rollno=student.id)
                    if studentInCourse:
                        seatnumber = mark[2][i]
                        if str(seatnumber) in seats:
                            present = True
                        else:
                            present = False
                        # m = seats.index(str(seatnumber))
                        k = str(date).split('/')
                        l = k[2]+"-"+k[1]+'-'+k[0]
                        save = AttendanceDaily.objects.create(rollno=student,coursecode=course,date=l,present=present)
                        save.save()
                except:
                    continue
        return courseHome(request,course_code)
    return HttpResponseRedirect(redirect)


def uploadPicture(request):
    redirect = checkIdentity(request,'adminstaff')
    if redirect == "":
        template = loader.get_template('adminStaff/_index.html')
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        if request.method == "POST":
            picture = request.FILES['picture']
            if picture:
                current.username.photo = picture
                current.username.save(update_fields=['photo',])
        feedbackList = Feedback.objects.all
        context = RequestContext(request, {'current': current, 'feedbackList': feedbackList, 'sent':"", })
        return HttpResponse(template.render(context))
    return HttpResponseRedirect(redirect)

def processUploadAttendance(request,course_code):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        if request.method == 'POST':
            form1 = read(request.POST, request.FILES)
            total = request.POST['date1']
            course = Course.objects.get(id= course_code)
            if form1.is_valid():
                newdoc = Document1(docfile = request.FILES['docfile'])
                newdoc.save()
                path = os.path.abspath(newdoc.docfile.url[1:])
                mark = np.genfromtxt(path, dtype='str', delimiter=',',unpack='True',skip_header=1)
                for i in range(250):
                    try:
                        # k = mark[1][i]
                        student = Student.objects.get(rollno=int(mark[1][i]))
                        studentInCourse = course.getStudents().filter(rollno=student.id)
                        if studentInCourse:
                            k = str(total).split('/')
                            l = k[2]+"-"+k[1]+'-'+k[0]
                            if mark[2][i][0] == 'P':
                                present = True
                            else:
                                present=False
                            save = AttendanceDaily.objects.create(rollno=student,coursecode=course,date=l,present=present)
                            save.save()
                    except:
                        continue
        return courseHome(request,course_code)
    return HttpResponseRedirect(redirect)

def processUploadMarks(request,course_code):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        if request.method == 'POST':
            form = DocumentForm(request.POST, request.FILES)
            total = request.POST['totalMarks']
            examName = request.POST['examName']
            course = Course.objects.get(id= course_code)
            if form.is_valid():
                newdoc = Document(docfile = request.FILES['docfile'])
                newdoc.save()
                path = os.path.abspath(newdoc.docfile.url[1:])
                mark = np.genfromtxt(path, dtype='str', delimiter=',',unpack='True',skip_header=1)
                for i in range(250):
                    # if mark[1][i]:
                    try:
                        student = Student.objects.get(rollno=int(mark[1][i]))
                        studentInCourse = course.getStudents().filter(rollno=student.id)
                        if studentInCourse:
                            looo = mark[2][i]
                            save = Marks.objects.create(rollno=student,category=examName,semester_date=course.semester_offered[0] + str(course.year),
                                coursecode=course,marks=int(mark[2][i]),total=int(total))
                            save.save()
                    except:
                        continue
        return courseHome(request,course_code)
    return HttpResponseRedirect(redirect)

def index(request):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        template = loader.get_template('adminStaff/_index.html')
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        feedbackList = Feedback.objects.all
        if request.method == 'POST':
            notification_message = request.POST['message']
            sendNotification(request, 'ALL', '', notification_message)
            sent = "Notification sent Successfully"
            context = RequestContext(request, {'current': current, 'feedbackList': feedbackList, 'sent':sent, })
        else:
            context = RequestContext(request, {'current': current, 'feedbackList': feedbackList, 'sent':"", })
        return HttpResponse(template.render(context))
    return HttpResponseRedirect(redirect)

def viewStudentProfile(request, roll_no):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        return studentViewStudentProfile(request, roll_no, 'adminStaff/_viewStudent.html', current)
    return HttpResponseRedirect(redirect)

def searchResults(request):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        return portalSearchResults(request, 'adminStaff/_searchResults.html', 'adminStaff', current)
    return HttpResponseRedirect(redirect)

def coursesList(request):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        template = loader.get_template('adminStaff/_coursesList.html')
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        if request.method == 'POST':
            course_input = request.POST['course_input']
            query = "SELECT * FROM portal_course WHERE coursename LIKE \'%"+course_input+"%\' OR coursecode LIKE \'%" +course_input+ "%\'"
            courseList = Course.objects.raw(query)
            view_all = "Search Results"
        else:    
            courseList = Course.objects.all
            view_all = "All"
        context = RequestContext(request, {'current': current, 'courseList': courseList, 'all':view_all, })
        return HttpResponse(template.render(context))
    return HttpResponseRedirect(redirect)


def updateMarks(request, course_code):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        if request.method == 'POST':
            category = request.POST['category']
            k = []
            if category == 'MidSem1':
                cat = "MD1"
                k = request.POST.getlist('MD1[]')
                k1 = request.POST.getlist('MD1T[]')
            elif category == 'MidSem2':
                cat = "MD2"
                k = request.POST.getlist('MD2[]')
                k1 = request.POST.getlist('MD2T[]')
            else:
                cat = "ESM"
                k = request.POST.getlist('ESM[]')
                k1 = request.POST.getlist('ESMT[]')
            names = request.POST.getlist('rollnos[]')
            UpdateList = zip(names,k,k1)
            course = Course.objects.filter(pk=course_code)[0]
            # return asf
            for name,marks,total in UpdateList:
                try:
                    Students = Marks.objects.get(coursecode=course.id, category=cat,rollno=name)
                    Students.marks = marks
                    Students.total = total
                    marks = marks
                    Students.save(update_fields=['marks','total'])
                except:
                    k = Student.objects.get(id=name)
                    if not marks:
                        marks = 0
                    if not total:
                        total = 0
                    l = Marks.objects.create(rollno=k,coursecode=course,category=cat,marks=float(int(marks)),total=float(int(total)))
                    l.save()
                #return ihuh
        template = loader.get_template('adminStaff/_updateMarks.html')
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        course = Course.objects.filter(pk=course_code)[0]
        course_semester = course.semester_offered
        if course_semester[0] == "M":
            course_semester = "Monsoon"
        else:
            course_semester = "Spring"
        faculty = course.getFaculty().name
        ListofStudents = course.getStudents()
        StudentName = []
        StudentID = []
        ListofMarks1 = []
        ListofMarks2 = []
        ListofMarks3 = []
        ListofTotal1 = []
        ListofTotal2 = []
        ListofTotal3 = []
        for student in ListofStudents:
            StudentName.append(student.rollno.name)
            StudentID.append(student.rollno.id)
            L1 = Marks.objects.filter(coursecode=course.id, category='MD1', rollno = student.rollno.id)
            L2 = Marks.objects.filter(coursecode=course.id, category='MD2', rollno = student.rollno.id)
            L3 = Marks.objects.filter(coursecode=course.id, category='ESM', rollno = student.rollno.id)
            if L1:
                ListofMarks1.append(L1[0].marks)
                ListofTotal1.append(L1[0].total)
            else:
                ListofMarks1.append([])
                ListofTotal1.append([])
            if L2:
                ListofMarks2.append(L2[0].marks)
                ListofTotal2.append(L2[0].total)
            else:
                ListofMarks2.append([])
                ListofTotal2.append([])
            if L3:
                ListofMarks3.append(L3[0].marks)
                ListofTotal3.append(L3[0].total)
            else:
                ListofMarks3.append([])
                ListofTotal3.append([])
        ListofMarks = zip(StudentID,StudentName,ListofMarks1,ListofTotal1,ListofMarks2,ListofTotal2,ListofMarks3,ListofTotal3)      
        # return adfa
        form = DocumentForm()
        context = RequestContext(request, {'current': current, 'course': course, 'faculty': faculty, 'course_semester': course_semester, 'ListofMarks': ListofMarks, 'form':form})
        return HttpResponse(template.render(context))
    return HttpResponseRedirect(redirect)

def updateAttendance(request, course_code):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        template = loader.get_template('adminStaff/_updateAttendance.html')
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        course = Course.objects.filter(pk=course_code)[0]
        course_semester = course.semester_offered
        if course_semester[0] == "M":
            course_semester = "Monsoon"
        else:
            course_semester = "Spring"
        faculty = course.getFaculty().name
        if request.method == "POST":
            ListofStudents = course.getStudents()
            period = request.POST['periods']
            period = AttendanceMonthly.objects.filter(id = int(period))
            if period:
                selectValue = period[0]
                attendance = []
                for student in ListofStudents:
                    l = student.id
                    k = student.rollno
                    total = AttendanceDaily.objects.filter(rollno=student.rollno, coursecode=course.id, present=True, date__range=(period[0].start_date, period[0].end_date))
                    attendance.append(total.count())
                    # return adf
                ListofStudents = zip(ListofStudents,attendance)
                total = period[0].classes_taken_place
                totalList = AttendanceMonthly.objects.filter(coursecode=course.id)
            else:
                selectValue = 0
                attendance = []
                for student in ListofStudents:
                    l = student.id
                    k = student.rollno
                    total = AttendanceDaily.objects.filter(rollno=student.rollno, coursecode=course.id, present=True)
                    attendance.append(total.count())
                    # return adf
                ListofStudents = zip(ListofStudents,attendance)
                total = AttendanceMonthly.objects.filter(coursecode=course.id).aggregate(Sum('classes_taken_place'))
                totalList = AttendanceMonthly.objects.filter(coursecode=course.id)
                # return wers
                total = total['classes_taken_place__sum']
                form1 = read()
            context = RequestContext(request, {'current': current, 'course': course, 'faculty': faculty,
             'course_semester': course_semester, 'ListofStudents': ListofStudents, 'total': total, 'totalList': totalList,'selectValue': selectValue,'form1':form1})
        else:
            selectValue = 0
            ListofStudents = course.getStudents()
            attendance = []
            for student in ListofStudents:
                l = student.id
                k = student.rollno
                total = AttendanceDaily.objects.filter(rollno=student.rollno, coursecode=course.id, present=True)
                attendance.append(total.count())
                # return adf
            ListofStudents = zip(ListofStudents,attendance)
            total = AttendanceMonthly.objects.filter(coursecode=course.id).aggregate(Sum('classes_taken_place'))
            totalList = AttendanceMonthly.objects.filter(coursecode=course.id)
            # return wers
            total = total['classes_taken_place__sum']
            form1 = read()
            context = RequestContext(request, {'current': current, 'course': course, 'faculty': faculty,
             'course_semester': course_semester, 'ListofStudents': ListofStudents, 'total': total, 'totalList': totalList, 'selectValue':selectValue,'form1':form1})
        return HttpResponse(template.render(context))
    return HttpResponseRedirect(redirect)

def courseHome(request, course_code):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        template = loader.get_template('adminStaff/_courseHome.html')
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        course = Course.objects.filter(pk=course_code)[0]
        course_semester = course.semester_offered
        if course_semester[0] == "M":
            course_semester = "Monsoon"
        else:
            course_semester = "Spring"
        faculty = course.getFaculty().name
        course = Course.objects.filter(id=course_code)[0]
        #query = "SELECT * FROM Students_record WHERE Students_record.coursecode_id = \'"+str(course.id)+"\' AND Students_record.semester_date = \'"+course.semester_offered[0]+str(course.year)+"\'"
        #ListofStudents = Record.objects.raw(query)
        ListofStudents = Record.objects.filter(coursecode=course.id)
        context = RequestContext(request, {'current': current, 'course': course, 'faculty': faculty, 'course_semester': course_semester, 'ListofStudents': ListofStudents})
        return HttpResponse(template.render(context))
    return HttpResponseRedirect(redirect)

def reports(request):
    redirect = checkIdentity(request, 'adminstaff')
    if redirect == "":
        current = AdminStaff.objects.filter(username=request.session['username'])[0]
        return Reports(request, current, 'adminStaff/_reports.html', 'adminStaff/_results.html','adminStaff')
    return HttpResponseRedirect(redirect)

def emailOrExport(request):
    if request.method == "POST":
        email = request.POST['email']
        k = request.POST.getlist('students[]')
        ListofQueries = request.POST['querylist']
        ListofQueries = ListofQueries.split(', ')
        ListofQueries.pop(0)
        ListofEmails = Student.objects.filter(rollno__in=k)
        exporttype = request.POST['exporttype']
        if email == '-1' and exporttype !='0':
            if exporttype == '1':
                if request.POST['exportemail'] == 'other' or request.POST['exportemail'] == 'me':
                    csvfile = StringIO.StringIO()
                    writer = csv.writer(csvfile)
                    writer.writerow(['Queries', ])
                    for each in ListofQueries:
                        writer.writerow([each, ])
                        writer.writerow([''])
                    writer.writerow(['Roll No', 'Full Name', 'CGPA', 'Programme', 'Gender', 'Batch'])
                    for student in ListofEmails:
                        current_CGPA = student.current_CGPA
                        if not current_CGPA:
                            current_CGPA = student.getCGPA
                        writer.writerow([student.rollno, student.name, current_CGPA, student.programme, student.gender, student.batch, ])
                    if request.POST['exportemail'] == 'other':
                        message = EmailMessage("Report","PFA the Report", "cspssad43@gmail.com" ,[ request.POST['otheruser'],])
                    else:
                        message = EmailMessage("Report","PFA the Report", "cspssad43@gmail.com" ,[ str(current.username),])
                    message.attach('Report.csv', csvfile.getvalue() , 'text/csv')
                    message.send()
                else:
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="Report.csv"'
                    writer = csv.writer(response)
                    writer.writerow(['Queries', ])
                    for each in ListofQueries:
                        writer.writerow([each, ])
                        writer.writerow([''])
                    writer.writerow(['Roll No', 'Full Name', 'CGPA', 'Programme', 'Gender', 'Batch'])
                    for student in ListofEmails:
                        current_CGPA = student.current_CGPA
                        if not current_CGPA:
                            current_CGPA = student.getCGPA
                            writer.writerow([student.rollno, student.name, current_CGPA, student.programme, student.gender, student.batch, ])
                    return response
        elif email != '-1':
            ListofPeople = ListofEmails.values_list('username', flat=True)
            Subject = request.POST['subject']
            Message = request.POST['message']
            if email == 'indi':
                for person in ListofPeople:
                    sendMail([person, ], Subject, Message)
            elif email == 'group':
                sendMail(ListofPeople, Subject, Message)
            elif email == 'me':
                sendMail([request.session['username'], ], Subject, Message)
            elif email == 'other':
                otheremail = request.POST['otheruserin']
                sendMail([otheremail,], Subject, Message)
            elif email == 'parents':
                for person in ListofEmails:
                    sendNotification(request, person, Subject, Message)
    return HttpResponseRedirect('/adminStaff/reports/')
