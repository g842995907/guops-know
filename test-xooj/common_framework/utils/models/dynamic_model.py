from django.db import models


def create_model(name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    """

    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)

    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    model = type(name, (models.Model,), attrs)

    return model


def create_table_model(model):
    from django.db import connection

    cursor = connection.cursor()
    try:
        sql = None
        with connection.schema_editor() as editor:
            editor.create_model(model)
            # sql = editor.deferred_sql
            # cursor.execute(sql)
    except Exception, e:
        pass
    finally:
        cursor.close()


def delete_table_model(model):
    from django.db import connection
    try:
        with connection.schema_editor() as editor:
            editor.delete_model(model)
    finally:
        pass