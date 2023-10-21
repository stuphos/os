from django.urls import include, re_path

try: from django.urls import URLPattern as RegexURLPattern, URLResolver as RegexURLResolver
except ImportError:
    from django.urls import RegexURLPattern, RegexURLResolver


# URL pattern objects
def patterns(name, *sequence):
    return list(sequence)

#from django.conf.urls import *



# class unpackableMatch:
#     # Allow unpacking of 
#     class pattern:
#         def __init__(self, *args, **kwd):
#             self.re = reCompile(*args, **kwd)

#         def match(self, *args, **kwd):
#             r = self.re.match(*args, **kwd)
#             if r is None:
#                 return r

#             return unpackableMatch(r)

#     def __init__(self, match):
#         self.match = match

#     def __iter__(self):
#         yield from iter(self.match.groups())


# def url(regex, view, default_args = None, name = None):
#     return RegexURLPattern(reCompile(regex), view, default_args, name)

url = re_path


# def include_urlpatterns(regex, urlpatterns):
#     return RegexURLResolver(reCompile(regex), urlpatterns, None)

class urlConfModule:
    def __init__(self, patterns):
        self.urlpatterns = patterns

def include_urlpatterns(regexp, urlpatterns):
    return re_path(regexp, include(urlConfModule(urlpatterns)))

