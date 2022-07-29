# coding:utf-8
import os
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from mlpi import software
from mlpi import const
import uuid

pool = ProcessPoolExecutor(max_workers=const.DEFAULT_MAX_WORKER)
software = software.create_software()


def init_minecraft():
    os.mkdir(".minecraft")
    os.mkdir(os.path.join(".minecraft", "versions"))


def get_java_version(path):
    version = subprocess.run('"{}" -version'.format(path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             encoding="utf-8", universal_newlines=True).stdout.split("\n")[1]
    return version


def search_java():
    results = {}
    paths = software.java_path
    for i in paths:
        if os.path.exists(i):
            for n in os.listdir(i):
                if os.path.exists(os.path.join(i, n, "bin", "javaw.exe")):
                    try:
                        results[os.path.join(i, n, "bin", "javaw.exe")] = get_java_version(
                            os.path.join(i, n, "bin", "java.exe"))
                    except OSError:
                        pass
                if os.path.exists(os.path.join(i, n, "bin", "jre", "javaw.exe")):
                    try:
                        results[os.path.join(i, n, "bin", "jre", "javaw.exe")] = get_java_version(
                            os.path.join(i, n, "bin", "jre", "java.exe"))
                    except OSError:
                        pass
    return results


def get_minecraft_version(minecraft_dir):
    versions = {}
    _versions = list(os.listdir(os.path.join(os.path.abspath(minecraft_dir), "versions")))
    if _versions:
        for i in _versions:
            if not os.path.exists(os.path.join(minecraft_dir, "versions", i, i + ".json")):
                versions[i] = "JSON Not Exists"
            elif not os.path.getsize(os.path.join(minecraft_dir, "versions", i, i + ".json")):
                versions[i] = "JSON is NULL"
            else:
                versions[i] = ""

    return versions


def get_args(_dict, key, default):
    try:
        return _dict[key]
    except KeyError:
        return default


def patch_str(string):
    return '"{}"'.format(string)


def test(_dict, key, value):
    try:
        if _dict[key] == value:
            return True
        else:
            return False
    except KeyError:
        return True


def get_jars(libraries, minecraft_dir):
    classpath = []
    for n in libraries:

        try:
            path = os.path.join(minecraft_dir, "libraries", *n["downloads"]["artifact"]["path"].split("/"))
        except KeyError:
            continue
        if path in classpath:
            continue
        _cache = path

        try:
            rules = n["rules"]

            for j in rules:
                action = j["action"]
                try:
                    if test(j["os"], "name", software.get_system_name()) and test(j["os"], "arch",
                                                                                  software.get_system_arch()):
                        if action == "disallow":
                            _cache = ""
                            break
                    else:
                        if action == "allow":
                            _cache = ""
                except KeyError:
                    if action == "disallow":
                        _cache = ""
        except KeyError:
            pass
        finally:
            if _cache:
                classpath.append(_cache)

    return classpath


def async_launch_game(minecraft_dir, version, username, java, **kwargs):
    pool.submit(launch_game, minecraft_dir, version, username, java, **kwargs)


def launch_game(minecraft_dir, version, username, java, **kwargs):
    minecraft_dir = os.path.abspath(minecraft_dir)
    jsonpath = os.path.join(minecraft_dir, "versions", version, version + ".json")
    jarpath = os.path.join(minecraft_dir, "versions", version, version + ".jar")
    jsondata = json.loads(open(jsonpath, "r", encoding="utf-8").read())
    args = ""
    args += " {} ".format(get_args(kwargs, "jvmargs", const.DEFAULT_JVM_ARGS))
    try:

        for i in jsondata["arguments"]["jvm"]:
            if type(i) == dict:
                action = i["rules"][0]["action"]
                if test(i["rules"][0]["os"], "name", software.get_system_name()) and test(i["rules"][0]["os"], "arch",
                                                                                          software.get_system_arch()):
                    if action == "allow":
                        if type(i["value"]) == list:
                            for j in i["value"]:
                                if " " in j:
                                    j = '{}="{}"'.format(j.split("=")[0], j.split("=")[1])
                                args += " {}".format(j)
                        else:

                            args += " {}".format(i["value"])
            else:

                if i == "${classpath}":
                    classpath = ";".join(get_jars(jsondata["libraries"], minecraft_dir))

                    args += " " + patch_str(classpath + ";" + jarpath)
                else:
                    i = i.replace("${natives_directory}", patch_str(
                        os.path.join(minecraft_dir, "versions", version, "{}-natives".format(version))))
                    if os.path.exists(os.path.join(minecraft_dir, "versions", version, "{}-natives".format(version))):
                        os.mkdir(os.path.join(minecraft_dir, "versions", version, "{}-natives".format(version)))
                    i = i.replace("${launcher_name}", patch_str((get_args(kwargs, "launcher_name", "") + "(MLPI)")))
                    i = i.replace("${launcher_version}", patch_str((get_args(kwargs, "launcher_version", ""))))
                    args += " {}".format(i)
        args += " -Xmn{}m -Xmx{}m {} ".format(get_args(kwargs, "min_memory", const.DEFAULT_MIN_MEMORY_SIZE),
                                              get_args(kwargs, "max_memory", const.DEFAULT_MAX_MEMORY_SIZE),
                                              jsondata["mainClass"])

        _args = []
        for i in jsondata["arguments"]["game"]:
            if type(i) == str:
                _args.append(i)

            else:
                pass

        args += " ".join(_args)

    except KeyError:
        args += "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump "
        args += " -Xmn{}m -Xmx{}m ".format(get_args(kwargs, "min_memory", const.DEFAULT_MIN_MEMORY_SIZE),
                                           get_args(kwargs, "max_memory", const.DEFAULT_MAX_MEMORY_SIZE))
        args += patch_str('-Djava.library.path={}'.format(
            os.path.join(minecraft_dir, "versions", version, "{}-natives".format(version))))
        if os.path.exists(os.path.join(minecraft_dir, "versions", version, "{}-natives".format(version))):
            os.mkdir(os.path.join(minecraft_dir, "versions", version, "{}-natives".format(version)))
        args += " -cp " + patch_str(";".join(get_jars(jsondata["libraries"], minecraft_dir)) + ";" + jarpath + ' ')
        args += " {} ".format(jsondata["mainClass"])
        args += jsondata["minecraftArguments"]
    _uuid = "".join(str(uuid.uuid1()).split("-")).upper()
    args = args.replace("${auth_player_name}", username)
    args = args.replace("${game_directory}", patch_str((os.path.abspath(minecraft_dir))))
    args = args.replace("${version_name}", patch_str(version))
    args = args.replace("${assets_root}", patch_str(os.path.join(minecraft_dir, "assets")))
    args = args.replace("${game_assets}", patch_str(os.path.join(minecraft_dir, "assets", "virtual", "legacy")))
    args = args.replace("${assets_index_name}", patch_str(jsondata["assetIndex"]["id"]))
    args = args.replace("${auth_uuid}", _uuid)
    args = args.replace("${auth_access_token}", _uuid)
    args = args.replace("${user_properties}", json.dumps({}))
    args = args.replace("${user_type}", "Legacy")
    args = args.replace("${version_type}", jsondata["type"])
    args = args.replace("${auth_session}", _uuid)
    args += " ".join([" --width", str(get_args(kwargs, "width", const.DEFAULT_SCREEN_WIDTH))])
    args += " ".join([" --height", str(get_args(kwargs, "height", const.DEFAULT_SCREEN_HEIGHT))])
    if get_args(kwargs, "fullscreen", False):
        args += " --fullscreen"
    if get_args(kwargs, "demo", False):
        args += " --demo"
    if get_args(kwargs, "server",""):
        args += " --server "+get_args(kwargs, "server","")
    if get_args(kwargs, "port",""):
        args += " --port "+get_args(kwargs, "port","")

    p=subprocess.Popen(patch_str(java) + " " + args, shell=True,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,encoding="utf-8", universal_newlines=True)
    p.wait()

