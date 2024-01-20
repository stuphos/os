Web Application Interconstruction

    'services/cpython/cythonOf' \
        ('./deployment-cache', code) \
            .active <- code:

        from queue import Queue

        class VM:
            class Task:
                class Runtime:
                    TaskQ: Queue


        def active(context: VM.Task.Runtime) -> int:
            return context.task.machine.TaskQ.empty()
