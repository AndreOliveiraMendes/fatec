def same_config(config, data):
    # Compare the relevant fields to determine if they are the same configuration
    return (
        config.get('smtp_server') == data.get('smtp_server') and
        config.get('smtp_port') == data.get('smtp_port') and
        config.get('username') == data.get('username') and
        config.get('mail_from') == data.get('mail_from') and
        config.get('use_tls') == data.get('use_tls')
    )