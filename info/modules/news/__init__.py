# 实现新闻详情页
from flask import Blueprint

news_blu = Blueprint('news', __name__,url_prefix='/news')

from .views import *