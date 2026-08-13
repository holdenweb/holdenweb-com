from airium import Airium

class ExtendedAirium(Airium):
    pass


a = ExtendedAirium()

a('<!DOCTYPE html>')
with a.html(lang="en"):
    with a.head():
        a.meta(charset="utf-8")
        a.link(href="http://localhost:10443/static/css/normalize.css", rel="stylesheet", type="text/css")
        a.link(href="http://localhost:10443/static/css/styles.css", rel="stylesheet", type="text/css")
        a.link(href="hp.css", rel="stylesheet", type="text/css")
        a.script(src="https://code.jquery.com/jquery-3.2.1.slim.min.js", integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN", crossorigin="anonymous")
        a.link(rel="stylesheet", type="text/css", href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css")
        a.script(src="https://unpkg.com/@popperjs/core@2")
        a.script(src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta/js/bootstrap.min.js", integrity="sha384-h0AbiXch4ZDo7tp9hKZ4TsHbi047NrKGLO3SEJAg45jXxnGIfYzk4Si90RDIqNm1", crossorigin="anonymous")
        a.title(_t="Airium example")
        with a.style():
            pass

    with a.body(klass="home-page-holdenweb"):
        with a.div(klass="container whole-page"):
            with a.div(klass="row"):
                with a.div(klass="col-md-12 bluebar"):
                    a.p(_t="blue bar goes here")

            with a.div(klass="row grey-background", id="top-stripe"):
                with a.div(klass="logo-holder absolute"):
                    a.img(src="https://holdenweb.com/static/images/logo.png", id="logo")
                a.div(klass="col-md-2", border_color="black")
                with a.div(klass="col-md-8 strapline"):
                    a.p(_t="What you'll need to know tomorrow")
                a.div(klass="col-md-2")

            with a.div(klass="row"):
                a.div(klass="col-md-2")
                with a.div(klass="col-md-8 navbar"):
                    a.p(_t="THIS  THAT  THE OTHER")
                a.div(klass="col-md-2")

        a.script(src="hp.js")


with open("hp.html", 'w') as f:
    f.write(str(a))
