import os
import subprocess
import platform

def open_in_musescore(xml_path: str, musescore_path: str = None) -> None:
    """
    Opens a MusicXML file in MuseScore.
    
    Parameters
    ----------
    xml_path : str
        Path to the MusicXML (.xml) file to open.
    musescore_path : str, optional
        Full path to the MuseScore executable. If None, the system default will be used.
        
    Raises
    ------
    FileNotFoundError
        If the XML file does not exist.
    """
    if not os.path.isfile(xml_path):
        raise FileNotFoundError(f"The XML file '{xml_path}' does not exist.")

    # Determine default MuseScore path depending on the OS
    if musescore_path is None:
        system = platform.system()
        if system == "Windows":
            musescore_path = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"
        elif system == "Darwin":  # macOS
            musescore_path = "/Applications/MuseScore 4.app/Contents/MacOS/mscore4"
        elif system == "Linux":
            musescore_path = "mscore"  # assume installed in PATH
        else:
            raise OSError("Unsupported operating system.")

    # Open the file
    try:
        subprocess.run([musescore_path, xml_path], check=True)
    except subprocess.CalledProcessError as e:
        print("Error opening MuseScore:", e)
