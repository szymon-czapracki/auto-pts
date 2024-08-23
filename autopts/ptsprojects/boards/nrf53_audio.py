#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Nordic Semiconductor ASA.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

import os

from .nrf5x import *
from autopts.bot.common import check_call

board_type = 'nrf5340_audio_dk_nrf5340_cpuapp'


def build_and_flash_core(zephyr_wd, build_dir, board, debugger_snr, configs, recover = False):
    build_dir = os.path.join(zephyr_wd, build_dir)
    check_call('rm -rf build/'.split(), cwd=build_dir)

    overlay = '-- -DCMAKE_C_FLAGS="-Werror"'
    for conf in configs:
        overlay += f' -D{conf}'
    cmd = ['west', 'build', '-b', board]
    cmd.extend(overlay.split())
    check_call(cmd, cwd=build_dir)
    
    build_name = str(build_dir).split('/')[-1]
    check_call("rm ./build_{}.zip || exit 0".format(build_name).split(), cwd=zephyr_wd)
    check_call("zip -r {}/build_{}.zip build -i '*.hex' '*.config'".format(zephyr_wd, build_name).split(), cwd=build_dir)

    cmd = ['west', 'flash', '--skip-rebuild', '-i', debugger_snr]
    if recover:
        cmd.append('--recover')
    check_call(cmd, cwd=build_dir)

def build_and_flash(zephyr_wd, board, debugger_snr, conf_file=None, *args):
    """Build and flash Zephyr binary
    :param zephyr_wd: Zephyr source path
    :param board: IUT
    :param debugger_snr serial number
    :param conf_file: configuration file to be used
    """
    source_dir = os.getenv("AUTOPTS_SOURCE_DIR_APP")
    if source_dir is None:
        source_dir = os.path.join('tests', 'bluetooth', 'tester')

    logging.debug("%s: %s %s %s %s", build_and_flash.__name__, zephyr_wd,
                  board, conf_file, source_dir)

    app_core_configs = []
    if conf_file and conf_file != 'default' and conf_file != 'prj.conf':
        app_core_configs = [f'OVERLAY_CONFIG=\'{conf_file}\'']

    build_and_flash_core(zephyr_wd,
                         source_dir,
                         board,
                         debugger_snr,
                         app_core_configs,
                         True)

    config_dir_net = os.getenv("AUTOPTS_SOURCE_DIR_NET")
    if config_dir_net is None:
        net_core_configs = [f'OVERLAY_CONFIG=\'nrf5340_cpunet_iso-bt_ll_sw_split.conf;'
                            f'../../../tests/bluetooth/tester/nrf5340_hci_ipc_cpunet.conf\'']
    else:
        conf_path = os.path.join(zephyr_wd, config_dir_net, 'hci_ipc.conf')
        net_core_configs = [f'OVERLAY_CONFIG=\'{conf_path}\'']

    build_and_flash_core(zephyr_wd,
                         os.path.join('samples', 'bluetooth', 'hci_ipc'),
                         'nrf5340_audio_dk_nrf5340_cpunet',
                         debugger_snr,
                         net_core_configs)