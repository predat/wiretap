#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
import yaml

import wiretap

__author__ = "Sylvain Maziere"


def parse_args(args):
    parser = argparse.ArgumentParser(
        prog='wiretap',
        description="Wiretap command line tool.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--server', '-s',
        default='localhost',
        help='Wiretap server to connect')

    sub_parser = parser.add_subparsers(
        title='commands',
        description='Command to execute',
        metavar='<command>',
        dest='command_name')
    sub_parser.required = True

    # project
    parser_createproject = sub_parser.add_parser(
        'create-project',
        help="Create a Wiretap project.")
    parser_createproject.add_argument(
        'name', help='Project name')
    parser_createproject.add_argument(
        '--width', '-fw', default='1920',
        help='Frame width (default: %(default)s)')
    parser_createproject.add_argument(
        '--height', '-fh', default='1080',
        help='Frame height (default: %(default)s)')
    parser_createproject.add_argument(
        '--fps', '-fps', default='25',
        help='Frame rate (default: %(default)s)')
    parser_createproject.add_argument(
        '--aspect', '-a', default='1.7778',
        help='Aspect ratio (default: %(default)s)')
    parser_createproject.add_argument(
        '--field', '-fd', default='PROGRESSIVE',
        help='Field dominance (default: %(default)s)',
        choices=['FIELD_1', 'FIELD_2', 'PROGRESSIVE'])
    parser_createproject.add_argument(
        '--depth', '-d', default='10-bit',
        help='Frame depth (default: %(default)s)',
        choices=['8-bit', '10-bit', '12-bit', '12-bit u', '16-bit fp'])
    parser_createproject.add_argument(
        '--description', help='Project description')
    parser_createproject.add_argument(
        '--setupdir', '-s', help='Setup directory')
    parser_createproject.add_argument(
        '--libraries-file', type=argparse.FileType('r'),
        help='YAML file describing Libraries to create in project.')

    # user
    parser_createuser = sub_parser.add_parser(
        'create-user',
        help="Create a Wiretap user.")
    parser_createuser.add_argument(
        'name', help="Flame User name")

    parser_deleteuser = sub_parser.add_parser(
        'delete-user',
        help="Delete a Wiretap user.")
    parser_deleteuser.add_argument(
        'name', help="Flame User name")

    return parser.parse_args(args)


def main(args):
    args = parse_args(args)

    if args.command_name == 'create-project':
        project_setings = {
            'FrameWidth': args.width,
            'FrameHeight': args.height,
            'FrameDepth': args.depth,
            'AspectRatio': args.aspect,
            'FrameRate': '%s fps' % args.fps,
            'FieldDominance': args.field,
            'Description': args.description if args.description else ""}

        if args.setupdir:
            project_setings['SetupDir'] = args.setupdir

        handler = wiretap.WiretapHandler(hostname=args.server)
        project = handler.create_project(args.name, project_setings)

        libs = dict()
        if args.libraries_file:
            try:
                libs = yaml.load(args.libraries_file.read())
            except Exception:
                pass

        if libs:
            for lib in libs.keys():
                handler._create_project_librairies(project, lib, libs[lib])

    elif args.command_name == 'create-user':
        handler = wiretap.WiretapHandler(hostname=args.server)
        handler.create_user(args.name)

    elif args.command_name == 'delete-user':
        handler = wiretap.WiretapHandler(hostname=args.server)
        handler.delete_user(args.name)


def run():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
