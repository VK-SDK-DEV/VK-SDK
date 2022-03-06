# v1.6
- [+] Segregate databases
- [+] Multi-database support
- [+] use_db parameter for structs (used db defined in config.json by default)
- [+] AuthBasedMethodExecutor, allows you to define callback on failed auth
- [+] imports.require function, acts like node.js require
- [+] Add some short paths for functions and classes
- [+] Struct(create_new), don't add db row if record wasn't found

# v1.5.3
- [=] Remove relations between Database class and AbstractLongPoll class

# v1.5 [With Love from DDBot]
- [+] New max_two_buttons strategy on keyboard
- [=] Bug fixes introduced with structs rewrite
- [+] after_text_matcher: match text on after function
- [=] Fix write(after) behaviour
- [+] Drop column if it's not existing in struct
- [=] Fix issues with initializing structs
- [+] MethodExecutor class, usefull to create your own method executors
- [+] AbstractLongPoll, BotLongPoll 

# v1.4
- [=] Every class now can behave like Thread class
- [=] thread.threaded - add this decorator to execute function in a thread
- [=] thread.requires_start - wait until bot will be started and execute function  
- [+] after keyword to user.write: set after func after write
- [=] Replace: ThreadedStruct and ThreadedDatabase with more elegant threading solution
- [=] ListExtension.join(separator, prefix, postix) - same behaviour as separator.join(Iterable)
- [=] Rewrite Struct
- [+] events
- [+] setExtension - += operation for sets

# v1.3
- [+] Autocreate path for database
- [+] Use relative imports
- [+] jsonExtension.load(file) -> jsonExtension.load(file, ident) for pretty json output later
- [+] StructByAction is now iterable

# v1.2
- [+] one_time parameter to ThreadedStruct constructor: don't cache created database in thread manager 
- [+] one_time parameter to ThreadedDatabase constructor: -//-
- [=] Don't pass arguments to function, created by @command decarator if function doesn't accept any
- [=] User class now caches avatar and user name on create
- [=] User class can be None if provided user_id is invalid
- [+] ListExtension.all: returns True, if function(item) returns True for all items in list

# v1.1
- [-] db.tasks
- [+] tasks to all threads

# v1.0
- [=] Start on adding versions
- [=] changed all Structs constructors (MyStruct(self.db, param1=param) -> MyStruct(param1=param))
- [+] ThreadedDatabase.select_one_struct
- [+] ThreadedDatabase.select_all_structs
- [+] ThreadedStruct