class DisMatchedJobException(RuntimeError):
    def __init__(self, job_name, user_name):
        super().__init__(f'"{job_name}" from anyhelper database dismatched in user "{user_name}"')


class UnknownAHPositionException(RuntimeError):
    def __init__(self, position_name):
        super().__init__(f'"{position_name}" is not in local table')


class NoCSRFException(RuntimeError):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
