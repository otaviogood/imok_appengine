import os, datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

# must import template before importing django stuff
from google.appengine.ext.db import djangoforms
try:
  from django import newforms as forms
except ImportError:
  from django import forms
import django.core.exceptions

import settings
from datastore import *
from imokutils import *
from imokforms import *

class DebugHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    self.render('debug.html', self.getContext(locals()))

def deleteAll(table):
  query = table.all()
  count = query.count()
  results = query.fetch(count)
  db.delete(results)

class ResetDbHandler(RequestHandlerPlus):
  def post(self):
    deleteAll(ImokUser)
    deleteAll(Phone)
    deleteAll(RegisteredEmail)
    deleteAll(Post)
    deleteAll(SmsMessage)
    self.render('resetdb.html', self.getContext(locals()))

class DebugPostHandler(RequestHandlerPlus):
  def post(self):
    user = users.get_current_user()
    okUser = ImokUser.all().filter('account =', user).get()
    
    p = Post(user=user, message='test message', lat=37., lon=-122.)
    p.unique_id = Post.gen_unique_key()
    p.put()

    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
    
    debug_output = []
    for registeredEmail in registeredEmailQuery:
      templateData = {
        'message': p.message,
        'link': p.permalink(self.request.host_url),
        'user': okUser,
        'unsubscribe_link': registeredEmail.permalink(self.request.host_url)
        }
      emailBody = template.render(settings.template_path('email.txt'), templateData)
      mail.send_mail(sender='imok.mailer@gmail.com',
                     to=registeredEmail.emailAddress,
                     subject="I'm OK",
                     body=emailBody)
      debug_output.append(emailBody)

    if debug_output:
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write("\n\n".join(debug_output))
      return
    
    self.redirect('/home')
    
def main():
  application = webapp.WSGIApplication([
    ('/debug', DebugHandler),
    ('/debug/resetdb', ResetDbHandler),
    ('/debug/post', DebugPostHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
