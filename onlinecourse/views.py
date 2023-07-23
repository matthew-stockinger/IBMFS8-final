from django.shortcuts import render
from django.http import HttpResponseRedirect

# for debug and dev
from django.http import HttpResponse
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic, View
from django.contrib.auth import login, logout, authenticate
from math import floor
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(request, "onlinecourse/user_registration_bootstrap.html", context)
    elif request.method == "POST":
        # Check if user exists
        username = request.POST["username"]
        password = request.POST["psw"]
        first_name = request.POST["firstname"]
        last_name = request.POST["lastname"]
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
            )
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context["message"] = "User already exists."
            return render(
                request, "onlinecourse/user_registration_bootstrap.html", context
            )


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["psw"]
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context["message"] = "Invalid username or password."
            return render(request, "onlinecourse/user_login_bootstrap.html", context)
    else:
        return render(request, "onlinecourse/user_login_bootstrap.html", context)


def logout_request(request):
    logout(request)
    return redirect("onlinecourse:index")


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


class CourseListView(generic.ListView):
    template_name = "onlinecourse/course_list_bootstrap.html"
    context_object_name = "course_list"

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by("-total_enrollment")[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = "onlinecourse/course_detail_bootstrap.html"


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode="honor")
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(
        reverse(viewname="onlinecourse:course_details", args=(course.id,))
    )


class Submit(View):
    # return {list of choice instances}
    def extract_user_choices(self, request):
        user_choices = []
        for key in request.POST:
            if key.startswith("question"):
                choice_strings = request.POST.getlist(key)
                choice_nums = map(lambda s: int(s[7:]), choice_strings)
                choices = map(lambda n: Choice.objects.get(pk=n), choice_nums)
                user_choices.extend(choices)
        return user_choices

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        user = request.user
        enrollment = Enrollment.objects.get(user=user, course=course)
        submission = Submission.objects.create(enrollment=enrollment)
        user_choices = self.extract_user_choices(request)
        for choice in user_choices:
            submission.choices.add(choice)

        return HttpResponseRedirect(
            reverse(
                viewname="onlinecourse:show_exam_result",
                args=(
                    course.id,
                    submission.id,
                ),
            )
        )


def show_exam_result(request, course_id, submission_id):
    course = Course.objects.get(id=course_id)
    submission = Submission.objects.get(id=submission_id)
    lesson = submission.choices.first().question.lesson_id
    questions = lesson.question_set.all()
    selected_ids = submission.choices.values_list("id", flat=True)

    # how many questions were 100% correct?
    num_questions_correct = 0
    for question in questions:
        if question.is_get_score(selected_ids):
            num_questions_correct += 1

    exam_grade = floor(num_questions_correct / questions.count() * 100)

    context = {"course": course, "selected_ids": selected_ids, "grade": exam_grade}

    debug_template = f"""
    <!DOCTYPE html>
    <html>
    <body>
    <p>{context}</p>
    </body>
    </html>
"""

    return HttpResponse(debug_template)
    # return render(request, "onlinecourse/exam_result_bootstrap.html", context)
