def test_qkit_load():
    import qkit
    qkit.cfg['run_id'] = "Test"
    qkit.cfg['user'] = "Automated Test"
    qkit.start()