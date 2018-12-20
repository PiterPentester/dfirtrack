from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django_q.tasks import async_task, result
from dfirtrack_main.forms import SystemCreatorForm
from dfirtrack_main.logger.default_logger import debug_logger, error_logger, warning_logger
from dfirtrack_main.models import System

@login_required(login_url="/login")
def systems_creator(request):
    """ function to create many systems at once (helper function to call the real function) """

    # form was valid to post
    if request.method == "POST":
        request_post = request.POST
        request_user = request.user

        # call async function
        async_task(
            "dfirtrack_main.creator.systems_creator.systems_creator_async",
            request_post,
            request_user,
            hook = "dfirtrack_main.creator.systems_creator.systems_creator_hook",
        )

        return redirect('/systems')

    # show empty form
    else:
        form = SystemCreatorForm(initial={
            'systemstatus': 2,
            'analysisstatus': 1,
        })

    # call logger
    debug_logger(str(request.user), " SYSTEM_CREATOR_ENTERED")
    return render(request, 'dfirtrack_main/system/systems_creator.html', {'form': form})

def systems_creator_async(request_post, request_user):
    """ function to create many systems at once """

    # call logger
    debug_logger(str(request_user), " SYSTEM_CREATOR_BEGIN")

    # exctract lines from systemlist (list results from request object via large text area)
    lines = request_post.get('systemlist').splitlines()

    # set counters
    lines_empty_counter = 0
    lines_nostring_counter = 0
    lines_long_counter = 0
    systems_existing_counter = 0
    systems_created_counter = 0

    # iterate over lines
    for line in lines:

        # skip emtpy lines
        if line == '':
            warning_logger(str(request_user), " SYSTEM_CREATOR_ROW_EMPTY")
            lines_empty_counter += 1
            continue

        # check line for string
        if not isinstance(line, str):
            warning_logger(str(request_user), " SYSTEM_CREATOR_NO_STRING")
            lines_nostring_counter += 1
            continue

        # check line for length of string
        if len(line) > 50:
            warning_logger(str(request_user), " SYSTEM_CREATOR_LONG_STRING")
            lines_long_counter += 1
            continue

        # check for existence of system
        system = System.objects.filter(system_name = line)
        if system.count() > 0:
            # call logger
            error_logger(str(request_user), " SYSTEM_CREATOR_SYSTEM_EXISTS " + "system_name:" + line)
            systems_existing_counter += 1
            # leave this loop because system with this systemname already exists
            continue

        # create form with request data
        form = SystemCreatorForm(request_post)

        # create system
        if form.is_valid():

            # don't save form yet
            system = form.save(commit=False)

            # set system_name
            system.system_name = line

            # set auto values
            system.system_created_by_user_id = request_user
            system.system_modified_by_user_id = request_user
            system.system_modify_time = timezone.now()

            # save object
            system.save()

            # save manytomany
            form.save_m2m()

            # call logger
            system.logger(str(request_user), ' SYSTEM_CREATOR_EXECUTED')
            systems_created_counter += 1

    # call logger
    debug_logger(str(request_user), " SYSTEM_CREATOR_END")

    #return counters for messages
    return(lines_empty_counter, lines_nostring_counter, lines_long_counter, systems_existing_counter, systems_created_counter)

def systems_creator_hook(task):

    print(str(task.result))

    # get counters out of task result
    #lines_empty_counter = task.result[0]
    #lines_nostring_counter = task.result[1]
    #lines_long_counter = task.result[2]
    #systems_existing_counter = task.result[3]
    #systems_created_counter = task.result[4]

    ## call final messages
    #if lines_empty_counter > 0:
    #    if lines_empty_counter == 1:
    #        messages.warning(request, str(lines_empty_counter) + ' submitted line was empty in last Systems Creator run.')
    #    else:
    #        messages.warning(request, str(lines_empty_counter) + ' submitted lines were empty in last Systems Creator run.')
    #if lines_nostring_counter > 0:
    #    if lines_nostring_counter == 1:
    #        messages.warning(request, str(lines_nostring_counter) + ' submitted line was no valid string in last Systems Creator run.')
    #    else:
    #        messages.warning(request, str(lines_nostring_counter) + ' submitted lines were no valid string in last Systems Creator run.')
    #if lines_long_counter > 0:
    #    if lines_long_counter == 1:
    #        messages.warning(request, str(lines_long_counter) + ' submitted line was too long in last Systems Creator run.')
    #    else:
    #        messages.warning(request, str(lines_long_counter) + ' submitted lines were too long in last Systems Creator run.')
    #if systems_created_counter > 0:
    #    if systems_created_counter == 1:
    #        messages.success(request, str(systems_created_counter) + ' system was created in last Systems Creator run.')
    #    else:
    #        messages.success(request, str(systems_created_counter) + ' systems were created in last Systems Creator run.')
    #if systems_existing_counter > 0:
    #    if systems_existing_counter == 1:
    #        messages.success(request, str(systems_existing_counter) + ' submitted line was too long in last Systems Creator run.')
    #    else:
    #        messages.success(request, str(systems_existing_counter) + ' submitted lines were too long in last Systems Creator run.')
