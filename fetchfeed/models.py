# -*- coding = utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class Tabs(models.Model):
    name = models.CharField('标签', max_length=70)
    user = models.ManyToManyField(User)

    def __str__(self):
        return self.name


class Feed(models.Model):
    feed_title = models.CharField(max_length=70)
    feed_link = models.URLField(max_length=1024)
    feed_desc = models.CharField(max_length=280)
    item_title = models.CharField(max_length=70)
    item_link = models.URLField(max_length=1024)
    item_desc = models.CharField(max_length=280)
    created_date = models.DateTimeField('Create date', auto_now_add=True)
    slug = models.SlugField(max_length=70, unique=True)
    tabs = models.ManyToManyField(Tabs)

    def __str__(self):
        return self.feed_title
