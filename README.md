# YetAnotherDisk ШБР 2022

Что внутри?
===========
Приложение упаковано в Docker-контейнер и разворачивается с помощью Ansible.

Внутри Docker-контейнера доступны две команды: :shell:`YetAnotherDisk-db` — утилита
для управления состоянием базы данных и :shell:`YetAnotherDisk-api` — утилита для 
запуска REST API сервиса.

Как использовать?
=================
Как применить миграции:

.. code-block:: shell

    sudo docker run -it -p 80:80 --net=host  \
    -e YETANOTHERDISK_PG_URL=postgresql://user:hackme@localhost/YetAnotherDisk \
    ivasnev/yet_another_disk

Как запустить REST API сервис локально на порту 80:

.. code-block:: shell

    sudo docker run -it -p 80:8081 \
        -e YETANOTHERDISK_PG_URL=postgresql://user:hackme@localhost/YetAnotherDisk \
        ivasnev/yet_another_disk

Все доступные опции запуска любой команды можно получить с помощью
аргумента :shell:`--help`:

.. code-block:: shell

    docker run ivasnev/yet_another_disk YetAnotherDisk-db --help
    docker run ivasnev/yet_another_disk YetAnotherDisk-api --help

Опции для запуска можно указывать как аргументами командной строки, так и
переменными окружения с префиксом :shell:`YETANOTHERDISK` (например: вместо аргумента
:shell:`--pg-url` можно воспользоваться :shell:`YETANOTHERDISK_PG_URL`).

Как развернуть?
---------------
Чтобы развернуть и запустить сервис на серверах, добавьте список серверов в файл
deploy/hosts.ini (с установленной Ubuntu) и выполните команды:

.. code-block:: shell

    cd deploy
    ansible-playbook -i hosts.ini --user=root deploy.yml

Разработка
==========

Быстрые команды
---------------
* :shell:`make` Отобразить список доступных команд
* :shell:`make devenv` Создать и настроить виртуальное окружение для разработки
* :shell:`make postgres` Поднять Docker-контейнер с PostgreSQL
* :shell:`make clean` Удалить файлы, созданные модулем `distutils`_
* :shell:`make sdist` Создать `source distribution`_
* :shell:`make docker` Собрать Docker-образ
* :shell:`make upload` Загрузить Docker-образ на hub.docker.com

.. _pylama: https://github.com/klen/pylama
.. _distutils: https://docs.python.org/3/library/distutils.html
.. _source distribution: https://packaging.python.org/glossary/

Как подготовить окружение для разработки?
-----------------------------------------
.. code-block:: shell

    make devenv
    make postgres
    source env/bin/activate
    YetAnotherDisk-db upgrade head
    YetAnotherDisk-api

После запуска команд приложение начнет слушать запросы на 0.0.0.0:8081.
Для отладки в PyCharm необходимо запустить :shell:`env/bin/YetAnotherDisk-api`.




