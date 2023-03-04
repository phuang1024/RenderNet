# RenderFarm

Render farm system for Blender.

## Usage

This render farm program has 3 user types:

- Server: Centralized location for communication between all other users.
- Worker: Requests work (files to render) from and to the server.
- Client: Creates new jobs on the server (which are then sent to workers).

You can run multiple instances on one computer. For example, you can run both a server and worker
on one computer, and that computer will both coordinate work and do the work as well.

## CLI

On the first usage, the program will request config information. You can edit it later in `config.json`

### Server

```bash
python main.py server
```

This will start the server indefinitely.

### Worker

```bash
python main.py worker
```

This will start the worker indefinitely.

### Client

```bash
python main.py client /path/to/blend.blend /path/to/save/renders/ frames
```

Create a new job and wait for it to finish.
Currently, there is no way to resume waiting for a job if you close the terminal.

Enter frames in Python slice syntax; i.e. `start:stop:step` with inclusive start and exclusive step.

- `1:10:2` means frames `(1, 3, 5, 7, 9)`
- `1:10:2,12:15` means frames `(1, 3, ..., 9, 12, 13, 14, 15)`
