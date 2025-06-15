# about project

this is a open source project to deal with laboratory reservation

# project structure

the project have the following structure

```
.
├── .env                      # environment
├── .env.example              # example file
├── .gitignore                # ignore sensible files
├── Readme.md                 # this file
├── auxiliar_template         # global template functions
│   └── auxiliar.py
├── config.py                 # configuration
├── decorators.py             # decorators
├── main.py                   # main entry point
├── models.py                 # database definition
├── requirements.txt          # requeriments
├── routes                    # define the backend functions
│   ├── auth.py               # autentication related
│   ├── default.py            # others
│   └── error.py              # error handling
├── schema.sql                # database structure
├── start-dev.bat             # quick startup file
├── static                    # static files
│   └── images
│       ├── favicon.png
│       └── favicon.svg
└── templates                 # front end stuff
    ├── 404.html              # not found template
    ├── admin.html            # admin page
    ├── auth                  # auth related
    │   ├── login.html
    │   ├── login_fail.html
    │   ├── login_sucess.html
    │   └── logout.html
    ├── base                  # base template
    ├── database              # database related
    │   └── usuarios.html
    └── homepage.html         # initial page
```

- .env: defines environment variables, you can check .env.example for what variables are defined
- .gitignore: ignore all sensible or unimportant files
- Reademe.md: this file, brief project explanation
- auxiliar_template: function that can be used inside jinja template
- config.py: main configuration file for project
- decorators.py: have all decorators that routes use
- main.py: the main entry point of project
- models.py: define the database schema
- requeriments.txt: the file listing all the libraly the project uses
- routes: the backend routes, divided by sections
- schema.sql: the databse structure
- static: static files for site (favicon, css, jss)
- templates: the front end pages that are rendered, separated by sections
- temaples/base: the default page all pages are based on