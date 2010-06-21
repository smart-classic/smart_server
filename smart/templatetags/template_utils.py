import time
from django import template
from django.http import HttpResponse
from django.template import Context, loader
from django.template.defaultfilters import stringfilter
# from smart.models import Document
from smart.lib import iso8601

register = template.Library()

@register.filter
@stringfilter
def check_empty(value):
  if value == 'None' or value == '':
    return ''
  else:
    return value
check_empty.is_safe = True


@register.filter
@stringfilter
def get_doc_obj(doc_id):
  try:
    return loader.get_template('document.xml').render(Context({'doc': Document.objects.get(id=doc_id)}))
  except:
    return ""
get_doc_obj.is_safe = True

@register.filter
@stringfilter
def format_iso8601(timestamp):
  if timestamp and not timestamp == 'None':
    if timestamp.find('.') > 0:
      return iso8601.parse_date(timestamp[0:timestamp.find('.')]).isoformat()
    return iso8601.parse_date(timestamp).isoformat()
  else:
    return ""
format_iso8601.is_safe = True
