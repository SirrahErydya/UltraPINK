from django.contrib import admin
import som.models as sm


admin.site.register(sm.SOM)
admin.site.register(sm.Prototype)
admin.site.register(sm.DataPoint)
admin.site.register(sm.Label)
