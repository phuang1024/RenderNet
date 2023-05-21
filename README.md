# RenderNet

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

**First, create a job.**

```bash
python main.py create /path/to/blend.blend frames
```

The program will print out a **Job ID**. Take note of it to download the results.

Enter frames in Python slice syntax; i.e. `start:stop:step` with inclusive start and exclusive step.

- `1:10:2` means frames `(1, 3, 5, 7, 9)`
- `1:10:2,12:15` means frames `(1, 3, ..., 9, 12, 13, 14)`

**Then, download the results.**

```bash
python main.py download job_id /path/to/save/
```

Enter the Job ID obtained from the previous command. You can start and stop this command any
time, and it will resume downloading.
