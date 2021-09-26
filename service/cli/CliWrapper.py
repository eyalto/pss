import subprocess
import select
import logging

class Cli:
    def __init__(self, command, logger, stdout_log_level=logging.INFO, stderr_log_level=logging.ERROR):
        self.command = command
        self.logger = logger
        self.stdout_log_level = stdout_log_level
        self.stderr_log_level = stderr_log_level
        self.errors = []


    def check_io(self, child, log_level):
        ready_to_read = select.select([child.stdout, child.stderr], [], [], 1000)[0]
        for io in ready_to_read:
            line = io.readline()
            if line.decode("utf-8").strip() != '':
                if log_level[io] == self.stderr_log_level:
                    self.errors.append(line[:-1].decode())
                self.logger.log(log_level[io], line[:-1])

    def run(self, command_line_args=None,env=None):
        if isinstance(self.command, list):
            command = self.command
        else:
            command = [self.command]

        if command_line_args is not None:
            command.extend(command_line_args)

        self.logger.info('Subprocess: about to run: ' + " ".join(command))
        try:
            child = subprocess.Popen(command,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     env=env)

            log_level = {child.stdout: self.stdout_log_level,
                         child.stderr: self.stderr_log_level}
            # keep checking stdout/stderr until the child exits
            while child.poll() is None:
                self.check_io(child, log_level)

            self.check_io(child, log_level)  # check again to catch anything after the process exits

            rc = child.wait()
            child.stdout.close()
            child.stderr.close()
            self.logger.info('Subprocess finished %s ' % (str(rc)))
            err_msg = '\n'.join(self.errors)
            return rc, err_msg

        except (OSError, subprocess.CalledProcessError) as exception:
            self.logger.error('Exception occured: ' + str(exception))
            self.logger.info('Subprocess failed')
            return -1, str(exception)
