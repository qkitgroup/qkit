import qkit



#Check if we are using the new data structure and if we have set user and RunID
if qkit.cfg.get('new_data_structure', False):
    try:
        import ipywidgets as widgets
        from IPython.display import display
    
        b = widgets.Button(
                description='Done.',
                disabled=False,
                button_style='info',  # 'success', 'info', 'warning', 'danger' or ''
        )
    
        b.f1 = widgets.Text(
                value=str(qkit.cfg.get('run_id','')),
                placeholder='RUN_ID',
                description='Please check: Run ID',
                disabled=False
        )
        
        if str(qkit.cfg.get('run_id','')) == '':
            b.f1.border_color = 'red'
    
        b.f2 = widgets.Text(
                value=str(qkit.cfg.get('user','')),
                placeholder='USER',
                description='user name',
                disabled=False
        )
    
        if str(qkit.cfg.get('user', '')) == '':
            b.f2.border_color = 'red'
            
        def clickfunc(btn):
            qkit.cfg['run_id'] = b.f1.value
            qkit.cfg['user'] = b.f2.value
            b.f1.disabled =True#close()
            b.f1.border_color = '#cccccc'
            b.f2.border_color = '#cccccc'
            b.f2.disabled=True#close()
            b.disabled=True#()
            b.button_style ='success'
    
    
        b.on_click(clickfunc)
        display(widgets.HBox([b.f1, b.f2, b]))
    except ImportError:
        import logging
        if not 'run_id' in qkit.cfg:
           logging.error('You are using the new data structure, but you did not specify a run ID. Please set qkit.cfg["run_id"] NOW to avoid searching your data.')
        if not 'user' in qkit.cfg:
           logging.error('You are using the new data structure, but you did not specify a username. Please set qkit.cfg["user"] NOW to avoid searching your data.')