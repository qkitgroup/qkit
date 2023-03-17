import qkit

# Check if we are using the new data structure and if we have set user and RunID
if 'new_data_structure' in qkit.cfg:
    raise ValueError(__name__+": Please use qkit.cfg['datafolder_structure'] = 1 instead of qkit.cfg['new_data_structure'] in your config.")
if qkit.cfg.get('datafolder_structure', 1) == 2:
    # noinspection SpellCheckingInspection
    try:
        import ipywidgets as widgets
        from IPython.display import display
        
        b = widgets.Button(
                description='Please Check!',
                disabled=False,
                button_style='info',  # 'success', 'info', 'warning', 'danger' or ''
        )
        
        b.f1 = widgets.Text(
                value=str(qkit.cfg.get('run_id', '')).upper(),
                placeholder='***RUN_ID IS EMPTY***',
                description='Please check: Run ID',
                disabled=False,
                style={'description_width': 'initial'}
        )
        
        b.f2 = widgets.Text(
                value=str(qkit.cfg.get('user', '')),
                placeholder='***USER IS EMPTY***',
                description='user name',
                disabled=False,
                style={'description_width': 'initial'}
        )
        if not qkit.cfg.get('run_id', False):
            b.f1.border_color = 'red'
            b.button_style = 'danger'
        
        if not qkit.cfg.get('user', False):
            b.f2.border_color = 'red'
            b.button_style = 'danger'
        
        
        def clickfunc(btn):
            if not b.f1.value:
                raise ValueError("RUN_ID is still empty!")
            if not b.f2.value:
                raise ValueError("USER is still empty!")
            qkit.cfg['run_id'] = b.f1.value.upper()
            qkit.cfg['user'] = b.f2.value
            btn.f1.disabled = True  # close()
            btn.f1.border_color = '#cccccc'
            btn.f2.border_color = '#cccccc'
            btn.f2.disabled = True  # close()
            btn.disabled = True  # ()
            btn.button_style = 'success'
            btn.description = 'Done.'
        
        
        b.on_click(clickfunc)
        display(widgets.HBox([b.f1, b.f2, b]))
    except ImportError:
        import logging
        
        if 'run_id' not in qkit.cfg:
            logging.error(
                    'You are using the new data structure, but you did not specify a run ID. Please set qkit.cfg["run_id"] NOW to avoid searching your data.')
        if 'user' not in qkit.cfg:
            logging.error(
                    'You are using the new data structure, but you did not specify a username. Please set qkit.cfg["user"] NOW to avoid searching your data.')
