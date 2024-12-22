import os
import sys
# import pkg_resources
import importlib.metadata
import subprocess
import atexit
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store the subprocess for the tunnel
tunnel_process = None
rsd_address = None
server_host = ""
server_port = 5000


def ensure_pymobiledevice3_developer_scripts_customized():
    """
    Find the location of the pymobiledevice3 cli/developer python script file and do some modification to it.
    """

    # Get the pymobiledevice3 package path
    # pymobiledevice3_pkg_path = pkg_resources.get_distribution("pymobiledevice3").location
    pymobiledevice3_location = importlib.metadata.distribution("pymobiledevice3").locate_file("") # get the location of the package

    # Get the pymobiledevice3 developer script path
    pymobiledevice3_dev_script_path = os.path.join(pymobiledevice3_location, "pymobiledevice3", "cli", "developer.py")
    # print(f"pymobiledevice3 developer script path: {pymobiledevice3_dev_script_path}")

    if not os.path.exists(pymobiledevice3_dev_script_path):
        print("\033[91mThe pymobiledevice3 developer script file is not found. \033[0m")
        return

    # Read the content of the developer script
    with open(pymobiledevice3_dev_script_path, "r") as f:
        dev_script_content = f.read()

        # Modify the developer script content
        set_loc_method_index = dev_script_content.find("def dvt_simulate_location_set")
        if set_loc_method_index == -1:
            print("\033[91mFailed to find the method to modify in the developer script. \033[0m")
            return
        cmd_wait_index = dev_script_content.find("OSUTILS.wait_return()", set_loc_method_index)
        if cmd_wait_index == -1:
            print("\033[91mFailed to find the command wait index in the developer script. \033[0m")
            return
        if dev_script_content[cmd_wait_index-1] == "#" or dev_script_content[cmd_wait_index-2] == "#":
            print("\033[92mThe command wait line is already commented out in the developer script. \033[0m")
            return
        
        # replace the wait command text as commented out
        dev_script_content = dev_script_content[:cmd_wait_index] + "#" + dev_script_content[cmd_wait_index:]

        # save the modified content back to the developer script
        with open(pymobiledevice3_dev_script_path, "w") as f:
            f.write(dev_script_content)
        print("\033[92mThe command wait line has been commented out in the developer script. \033[0m")
        print("")


def start_tunnel():
    """
    Start the pymobiledevice3 tunnel and extract the --rsd address.
    """
    global tunnel_process, rsd_address
    try:
        # Start the tunnel command
        tunnel_process = subprocess.Popen(
            ["python", "-m", "pymobiledevice3", "remote", "tunneld"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # if the tunnel process is not started correctly, print error message in console stderr in red color
        if tunnel_process.poll() is not None:
            print("\033[91mError starting tunnel. \033[0m")
            return

        # Parse the output to get the --rsd address
        rsd_address_line = None
        for line in iter(tunnel_process.stdout.readline, ''):
            # print(line.strip())  # Print tunnel output to console
            if "Created tunnel --rsd" in line:
                rsd_address_line = line.strip()
                break
        if rsd_address_line is None:
            print("\033[91mError getting the --rsd address. \033[0m")
            return
        
        rsd_start_index = rsd_address_line.find("--rsd")
        rsd_address = rsd_address_line[rsd_start_index:].strip()
        print(f"Extracted RSD Address: {rsd_address}")

    except Exception as e:
        print(f"Error starting tunnel: {e}")
    
    if rsd_address is None or len(rsd_address) == 0:
        # remote tunnel is not established correctly, print error message in console stderr in red color
        print("\033[91mRemote tunnel is not established correctly, please check the device connection and start agent again.\033[0m")


def stop_tunnel():
    """
    Terminate the tunnel subprocess.
    """
    global tunnel_process
    if tunnel_process and tunnel_process.poll() is None:
        tunnel_process.terminate()
        print("Tunnel session terminated.")

# Register the stop_tunnel function to be called on server exit
atexit.register(stop_tunnel)

@app.route('/', methods=['GET'])
def get_server_info():
    """
    Default Page to show general server information.
    """

    server_info = f"""
    <h1>Mock GPS Agent Server</h1>
    <ul>
        <li><b>IOS Device Lockdown Tunnel:</b> {rsd_address}</li>
        <li><b>Server is running on:</b> http://{server_host}:{server_port}</li>
        <li>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><b>GET / :</b> Show this general server information</li>
                <li><b>POST /setlocation :</b> Set mock gps location on connected IOS device</li>
                <li><b>POST /execute :</b> Execute a generic terminal/cli command</li>
            </ul>
        </li>
    </ul>
    """

    return server_info

@app.route('/devices', methods=['GET'])
def get_ios_devices():
    """
    REST endpoint to show all connected (USB or Network) IOS devices.
    """

    try:
        # Execute the command
        list_devices_cmd = f"pymobiledevice3 usbmux list"
        result = subprocess.run(list_devices_cmd, shell=True, text=True, capture_output=True, check=True)
        cmd_output = result.stdout
        
        # write the cmd_output(json text) into response as application/json content type
        return cmd_output
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/setlocation', methods=['POST'])
def set_device_location():
    """
    REST endpoint to set device mock location via POST request.
    """
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')

    if not lat or not lon:
        return jsonify({"error": "No (longitude, latitude) info provided"}), 400

    try:
        # Execute the command
        setloc_cmd = f"pymobiledevice3 developer dvt simulate-location set {rsd_address} -- {lat} {lon}"
        print(f"Gonna execute command: {setloc_cmd}")
        result = subprocess.run(setloc_cmd, shell=True, text=True, capture_output=False, check=True)
        cmd_output = f"set device location to ({lon}, {lat})"
        
        return jsonify({"output": cmd_output})
        # return jsonify({"lon": lon, "lat": lat})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clearlocation', methods=['POST'])
def clear_device_location():
    """
    REST endpoint to clear device mock location via POST request.
    """
    try:
        # Execute the command
        clearloc_cmd = f"pymobiledevice3 developer dvt simulate-location clear {rsd_address}"
        print(f"Gonna execute command: {clearloc_cmd}")
        result = subprocess.run(clearloc_cmd, shell=True, text=True, capture_output=False, check=True)
        cmd_output = "cleared device location"
        
        return jsonify({"output": cmd_output})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/execute', methods=['POST'])
def execute_command():
    """
    REST endpoint to execute a command received via POST request.
    """
    data = request.json
    command = data.get('command')
    return_output = data.get('return_output')

    if not command:
        return jsonify({"error": "No command provided"}), 400

    try:
        # Execute the command
        result = subprocess.run(command, shell=True, text=True, capture_output=return_output, check=True)
        cmd_output = "command executed"
        if return_output:
            cmd_output = result.stdout
        return jsonify({"output": cmd_output})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    import argparse

    # Ensure the pymobiledevice3 developer script is customized
    ensure_pymobiledevice3_developer_scripts_customized()

    parser = argparse.ArgumentParser(description="Run the iOS Mock GPS Agent server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host address (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on (default: 5000).")
    args = parser.parse_args()

    server_host = args.host
    server_port = args.port

    # print out server is running message in green color
    print(f"\033[92mMockGPSAgent server is starting on http://{server_host}:{server_port} \033[0m")

    # Start the server
    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()

    try:            
        app.run(host=server_host, port=server_port)
    except KeyboardInterrupt:
        print("Server shutting down.")


if __name__ == "__main__":
    main()