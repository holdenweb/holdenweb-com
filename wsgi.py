from holdenweb import create_app

# Module-level for uwsgi, which imports `application` from here. Built here
# rather than at package import so that importing `holdenweb` (tests, alembic)
# does not demand a full production environment.
app = create_app()
application = app.wsgi_app

if __name__ == '__main__':
    app.run(port=8456, debug=True)
