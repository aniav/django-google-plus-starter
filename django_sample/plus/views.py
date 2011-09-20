import logging
import httplib2

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from apiclient.discovery import build
from django_sample.plus.models import CredentialsModel
from django_sample.plus.models import FlowModel
from oauth2client.django_orm import Storage
from oauth2client.client import OAuth2WebServerFlow

@login_required
def index(request):
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        flow = OAuth2WebServerFlow(client_id=settings.CLIENT_ID,
                                   client_secret=settings.CLIENT_SECRET,
                                   scope=settings.SCOPE,
                                   user_agent='plus-django-sample/1.0')

        authorize_url = flow.step1_get_authorize_url(settings.STEP2_URI)
        f = FlowModel(id=request.user, flow=flow)
        f.save()
        return HttpResponseRedirect(authorize_url)
    else:
        http = httplib2.Http()
        http = credential.authorize(http)
        service = build("plus", "v1", http=http)
        activts = service.activities()
        activitylist = activts.list(userId='me', collection='public').execute()
        logging.info(activitylist)

        return TemplateResponse(request, 'plus/welcome.html', {
            'activitylist': activitylist,
        })

@login_required
def auth_return(request):
    try:
      f = FlowModel.objects.get(id=request.user)
      credential = f.flow.step2_exchange(request.REQUEST)
      storage = Storage(CredentialsModel, 'id', request.user, 'credential')
      storage.put(credential)
      f.delete()
      return HttpResponseRedirect("/")
    except FlowModel.DoesNotExist:
      pass
