import sys
from django.utils.timezone import now

try:
    from django.db import models
except Exception:
    print("There was an error loading django modules. Do you have django installed?")
    sys.exit()

from django.conf import settings
import uuid


# Instructor model
class Instructor(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    full_time = models.BooleanField(default=True)
    total_learners = models.IntegerField()

    def __str__(self):
        return self.user.username


# Learner model
class Learner(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    STUDENT = "student"
    DEVELOPER = "developer"
    DATA_SCIENTIST = "data_scientist"
    DATABASE_ADMIN = "dba"
    OCCUPATION_CHOICES = [
        (STUDENT, "Student"),
        (DEVELOPER, "Developer"),
        (DATA_SCIENTIST, "Data Scientist"),
        (DATABASE_ADMIN, "Database Admin"),
    ]
    occupation = models.CharField(
        null=False, max_length=20, choices=OCCUPATION_CHOICES, default=STUDENT
    )
    social_link = models.URLField(max_length=200)

    def __str__(self):
        return self.user.username + "," + self.occupation


# Course model
class Course(models.Model):
    name = models.CharField(null=False, max_length=30, default="online course")
    image = models.ImageField(upload_to="course_images/")
    description = models.CharField(max_length=1000)
    pub_date = models.DateField(null=True)
    instructors = models.ManyToManyField(Instructor)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Enrollment")
    total_enrollment = models.IntegerField(default=0)
    is_enrolled = False

    def __str__(self):
        return "Name: " + self.name + "," + "Description: " + self.description


# Lesson model
class Lesson(models.Model):
    title = models.CharField(max_length=200, default="title")
    order = models.IntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()

    def __str__(self):
        return str(self.order) + ". " + self.title


# Enrollment model
# <HINT> Once a user enrolled a class, an enrollment entry should be created between the user and course
# And we could use the enrollment to track information such as exam submissions
class Enrollment(models.Model):
    AUDIT = "audit"
    HONOR = "honor"
    BETA = "BETA"
    COURSE_MODES = [(AUDIT, "Audit"), (HONOR, "Honor"), (BETA, "BETA")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(max_length=5, choices=COURSE_MODES, default=AUDIT)
    rating = models.FloatField(default=5.0)

    def __str__(self):
        return str(self.user) + " - " + str(self.course)


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson_id = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    grade = models.IntegerField()
    question_text = models.TextField(null=False)

    def __str__(self):
        if len(self.question_text) > 60:
            return self.question_text[:60] + "..."
        else:
            return self.question_text

    def is_get_score(self, selected_ids):
        print("question id = ", self.id)
        all_answers = self.choice_set.filter(is_correct=True).count()
        print("all_answers", all_answers)
        selected_correct = self.choice_set.filter(
            is_correct=True, id__in=selected_ids
        ).count()
        total_selected = self.choice_set.filter(id__in=selected_ids).count()
        print("selected_correct", selected_correct)
        print("total_selected", total_selected)
        if all_answers == selected_correct and all_answers == total_selected:
            return True
        else:
            return False


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, default=0)
    choice_text = models.TextField(null=False)
    is_correct = models.BooleanField()

    def __str__(self):
        choice_id_string = f"choice {self.id} - "
        if len(self.choice_text) > 60:
            return choice_id_string + self.choice_text[:60] + "..."
        else:
            return choice_id_string + self.choice_text


class Submission(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    choices = models.ManyToManyField(Choice)

    def __str__(self):
        choices_string_list = list(map(lambda c: str(c), self.choices.all()))
        return str(self.id) + str(choices_string_list)
