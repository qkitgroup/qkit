import os
import shutil
import time

import qt

qtlab_dir = qt.config['execdir']
todo_dir = os.path.join(qtlab_dir, 'batch','todo')
done_dir = os.path.join(qtlab_dir, 'batch','done')

def batch_start():

    if not os.path.isdir(todo_dir):
        os.makedirs(todo_dir)

    if not os.path.isdir(done_dir):
        os.makedirs(done_dir)

    print '\n==== Starting Batch Mode ====\n'
    print 'todo dir: %s ' % todo_dir
    print 'done dir: %s ' % done_dir
    print 'to leave batch mode push "stop" button, or drop _stop_ file in "todo dir"'
    print '\n=============================\n'

    reply = True
    while reply:
        reply = _batch_run_single_file()
        try:
            qt.flow.measurement_start()
            qt.flow.measurement_idle(2)
            qt.flow.measurement_end()
        except ValueError, valerror:
            if valerror.message == 'Human abort':
                print 'Human abort'
                return

def _batch_run_single_file():

    timestamp = time.strftime('%Y%m%d_%H%M%S_')

    todo_list = os.listdir(todo_dir)

    idx = -1
    for item in todo_list:
        idx += 1
        filename, ext = os.path.splitext(item)
        if ext != '.py':
            todo_list.pop(idx)
        if filename == '_stop_':
            shutil.os.remove(os.path.join(todo_dir,'_stop_'))
            return False

    if len(todo_list) == 0:
        return True

    todo_list.sort()
    next_on_list = todo_list[0]
    todo_fp = os.path.join(todo_dir,next_on_list)
    done_fp = os.path.join(done_dir,timestamp + next_on_list)

    print '\n===> Executing: %s\n' % next_on_list
    try:
        execfile(todo_fp)
        print '\n===> Finished Succesfully: %s\n' % next_on_list
        shutil.move(todo_fp,done_fp)
    except ValueError, valerror:
        if valerror.message == 'Human abort':
            print '\n===> Aborted by Human: %s\n' % next_on_list
            print 'Leaving batch mode'
            return False
        else:
            print '\n !! Error during execution !! \n'
            print '%r' % valerror
            fp, ext = os.path.splitext(done_fp)
            error_fp = fp + '.error'
            f = file(error_fp, 'w')
            f.write('%r' % valerror)
            f.close()
            print '\n===> Finished with Error: %s\n' % next_on_list
            shutil.move(todo_fp,done_fp)
    except Exception, err:
        print '\n !! Error during execution !! \n'
        print '%r' % err
        fp, ext = os.path.splitext(done_fp)
        error_fp = fp + '.error'
        f = file(error_fp, 'w')
        f.write('%r' % err)
        f.close()
        print '\n===> Finished with Error: %s\n' % next_on_list
        shutil.move(todo_fp,done_fp)

    return True
