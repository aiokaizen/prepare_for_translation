from datetime import datetime, timedelta
import pytz
import random
import json

from slugify import slugify

from django.db import models
from django.contrib.auth.models import User

from ckeditor_uploader.fields import RichTextUploadingField

from image_cropping import ImageRatioField

from portfolio import settings as portfolio_settings


class Category(models.Model):
    class Meta:
        verbose_name_plural = "Categories"

    name = models.CharField(verbose_name="Name", max_length=32)
    description = models.CharField(verbose_name="Description", max_length=128)

    def __str__(self):
        return self.name

    def get_posts(self):
        return Post.objects.filter(category=self)


class Author(User):
    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    avatar = models.ImageField("Avatar", null=True, blank=True)

    def get_posts(self):
        return Post.objects.filter(author=self)


class Post(models.Model):
    class Meta:
        ordering = ("-published_at", "-created_at")
        permissions = (("can_publish_post", "Can publish post"),)

    title = models.CharField(verbose_name="Title", max_length=256)
    slug = models.CharField(
        verbose_name="Slug", max_length=256, unique=True, blank=True
    )
    short_description = models.TextField(verbose_name="Short description")
    content = RichTextUploadingField(verbose_name="Content")
    category = models.ForeignKey(
        Category, verbose_name="Category", on_delete=models.PROTECT
    )
    tags = models.CharField(verbose_name="tags", max_length=256, default="", blank=True)
    image = models.ImageField(
        verbose_name="Image", upload_to="blog/", null=True, blank=True
    )
    thumbnail = ImageRatioField("image", "360x240")
    author = models.ForeignKey(
        Author, verbose_name="Author", on_delete=models.PROTECT, blank=True
    )
    created_at = models.DateTimeField(verbose_name="Created at", blank=True)
    published_at = models.DateTimeField(
        verbose_name="Published at", null=True, blank=True
    )
    updated_at = models.DateTimeField(verbose_name="Updated at", null=True, blank=True)
    # series = models.CharField(verbose_name="Series", max_length=128, default='', blank=True)

    def __str__(self):
        return f"{self.title}"

    def set_slug(self):
        """Set a slug for the post (This method doesn't save the object)"""

        original_slug = slugify(self.title) if not self.slug else self.slug
        slug = original_slug
        try:
            while True:
                Post.objects.get(slug=slug)
                slug = f"{original_slug}-{random.randint(10000, 99999)}"
        except Post.DoesNotExist:
            self.slug = slug

    def can_create(self, user):
        if not hasattr(user, "author"):
            return False, "You don't have the necessary permissions to create a post"
        return True, ""

    def create(self, user):
        can_create, msg = self.can_create()
        if not can_create:
            return False, msg

        self.set_slug()
        self.author = user.author
        self.created_at = datetime.now(tz=pytz.utc)
        self.save()
        return True, "The post has been successfully inserted."

    def can_update(self, user):
        if not hasattr(user, "author") or user.author != self.author:
            return False, "You don't have the necessary permissions to update this post"
        return True, ""

    def update(self, user):
        can_update, msg = self.can_update()
        if not can_update:
            return False, msg

        self.updated_at = datetime.now(tz=pytz.utc)
        self.save()
        return True, "The post has been successfully updated."

    def can_publish(self, user):
        if not user.hasperm("can_publish_post"):
            return False, "You don't have the required permissions to publish this post"
        return True, ""

    def publish(self, user):
        can_publish, msg = self.can_publish()
        if not can_publish:
            return False, msg

        self.updated_at = datetime.now(tz=pytz.utc)
        self.save()
        return True, "The post has been successfully published."

    @classmethod
    def list(cls, show_unpublished=False, *args, **kwargs):
        filters = {}
        if not show_unpublished:
            filters["published_at__lte"] = datetime.now(tz=pytz.utc)
        return cls.objects.filter(*args, **filters, **kwargs)

    def get_next_previous_posts(self):
        next, prev = None, None
        # if self.series:
        #     qset = Post.list(series=self.series)
        #     if qset.exists():
        #         next = qset.first()
        #         if qset.count() >
        return next, prev


class Message(models.Model):
    class Meta:
        ordering = ("-created_at",)

    name = models.CharField(verbose_name="Name", max_length=64, default="")
    email = models.EmailField(verbose_name="Email", default="")
    subject = models.CharField(
        verbose_name="Subject", max_length=128, default="", blank=True
    )
    message = models.TextField(verbose_name="Message", default="")
    created_at = models.DateTimeField(verbose_name="Created at")
    ip_address = models.CharField(
        verbose_name="IP address", max_length=32, blank=True, null=True
    )

    def __str__(self):
        return f"{self.name} - {self.subject}"

    def can_create_message(self):
        if self.exceeded_max_messages():
            return False, "You have exceeded the maximum number of allowed messages."
        return True, ""

    def create_message(self):
        can_create, msg = self.can_create_message()
        if not can_create:
            return False, msg

        self.created_at = datetime.now(tz=pytz.utc)
        self.save()
        return (
            True,
            "Your message has been sent successfully. Thank you for your interrest",
        )

    def exceeded_max_messages(self):
        id_filters = models.Q(ip_address=self.ip_address) | models.Q(email=self.email)
        interval = datetime.now() - timedelta(hours=5)
        old_messages = Message.objects.filter(id_filters, created_at__gt=interval)
        return old_messages.count() > 3

    @classmethod
    def list_messages(cls, *args, **kwargs):
        return cls.subject.filter(*args, **kwargs)


class EmailingList(models.Model):
    class Meta:
        verbose_name = "Emailing List"
        verbose_name_plural = "Emailing Lists"

    name = models.CharField(
        "Name",
        max_length=255,
        unique=True,
        choices=portfolio_settings.EMAILING_LIST_NAME_CHOICES,
    )
    emails = models.TextField("Emails list", default="", blank=True)

    def __str__(self):
        return self.get_name_display()

    def get_emails_list(self):
        emails = json.loads(self.emails) if self.emails else []
        return emails

    def subscribe(self, email):
        emails = self.get_emails_list()
        if email not in emails:
            emails.append(email)
            self.emails = json.dumps(emails)
            self.save()
        return (
            True,
            "You have subscribed to my newsletter updates. Thank you for joining in :)",
        )

    def unsubscribe(self, email):
        emails = self.get_emails_list()
        try:
            emails.remove(email)
            self.emails = json.dumps(emails)
            self.save()
            return (
                True,
                "You have been unsubscribed from my newsletter updates :(. You are welcomed to join back in in any time ;).",
            )
        except ValueError:
            return False, "This email address does not exists in my email list :/."

    @classmethod
    def emailing_list_factory(cls, name):
        """
        This method returns an emailing list object with a specific name.
        If the object does not exist, it creates a new instance and returns it.
        """
        emailing_list, c = cls.objects.get_or_create(name=name)
        return emailing_list
