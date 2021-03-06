# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Spanish_Inspire_Catastral_Downloader
                                 A QGIS plugin
 Spanish Inspire Catastral Downloader
                              -------------------
        begin                : 2017-06-18
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Patricio Soriano :: SIGdeletras.com
        email                : pasoriano@sigdeletras.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import urllib.request
import zipfile
import urllib
from urllib import request, parse

#TimeOut para la descarga de 5 segundos
import socket

# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import Qt
#from PyQt5 import QtCore, QtGui, QtWidgets
import os
import shutil
#from PyQt5.QtWidgets import QDialog
#For Debug
try:
    import sys
    from pydevd import *
except:
    None
 
try:
    from qgis.core import Qgis
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5 import uic
    QT_VERSION=5
    os.environ['QT_API'] = 'pyqt5'
except:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4 import uic
    from qgis.core import QgsMapLayerRegistry
    QT_VERSION=4
    
import os.path
from qgis.core import *

#import resources
from .resources import *

from .Spanish_Inspire_Catastral_Downloader_dialog import Spanish_Inspire_Catastral_DownloaderDialog
from .listamuni import *
from qgis.core import QgsProject
from qgis.gui import QgsMessageBar


listProvincias = LISTPROV
listMunicipios = LISTMUNI

codprov = ''
codmuni = ''
 
from .Config import _proxy
from .Config import _port

class Spanish_Inspire_Catastral_Downloader:
    """QGIS Plugin Implementation."""

    def __init__(self , iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.msgBar = iface.messageBar()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir ,
            'i18n' ,
            'Spanish_Inspire_Catastral_Downloader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Spanish Inspire Catastral Downloader')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Spanish_Inspire_Catastral_Downloader')
        self.toolbar.setObjectName(u'Spanish_Inspire_Catastral_Downloader')
        
        socket.setdefaulttimeout(5)

    # noinspection PyMethodMayBeStatic
    def tr(self , message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Spanish_Inspire_Catastral_Downloader' , message)

    def add_action(
            self ,
            icon_path ,
            text ,
            callback ,
            enabled_flag=True ,
            add_to_menu=True ,
            add_to_toolbar=True ,
            status_tip=None ,
            whats_this=None ,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = Spanish_Inspire_Catastral_DownloaderDialog()
        self.dlg.setWindowFlags(Qt.WindowSystemMenuHint | Qt.WindowTitleHint) 
        

        icon = QIcon(icon_path)
        action = QAction(icon , text , parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu ,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Spanish_Inspire_Catastral_Downloader/icon.png'
        self.add_action(
            icon_path ,
            text=self.tr(u'&Spanish Inspire Catastral Downloader') ,
            callback=self.run ,
            parent=self.iface.mainWindow())

        self.dlg.pushButton_select_path.clicked.connect(self.select_output_folder)
        self.dlg.pushButton_run.clicked.connect(self.download)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Spanish Inspire Catastral Downloader') ,
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_output_folder(self):
        """Select output folder"""

        self.dlg.lineEdit_path.clear()
        folder = QFileDialog.getExistingDirectory(self.dlg , "Select folder")
        self.dlg.lineEdit_path.setText(folder)

    def not_data(self):
        """Message for fields without information"""
        self.msgBar.pushMessage('Completar datos de municipio o indicar la ruta de descarga' , level=QgsMessageBar.INFO, duration=3)

    def filter_municipality(self , index):
        """Message for fields without information"""

        filtroprovincia = self.dlg.comboBox_province.currentText()
        self.dlg.comboBox_municipality.clear()

        self.dlg.comboBox_municipality.addItems([muni for muni in listMunicipios if muni[0:2] == filtroprovincia[0:2]])

        inecode_catastro = self.dlg.comboBox_municipality.currentText()

        codprov = inecode_catastro[0:2]
        codmuni = inecode_catastro[0:5]

    #Progress Download
    def reporthook(self,blocknum, blocksize, totalsize):
        readsofar = blocknum * blocksize
        if totalsize > 0:
            percent = readsofar * 1e2 / totalsize
            self.dlg.progressBar.setValue(int(percent))
    
    #Ser Proxy
    def set_proxy(self):
        proxy_handler = request.ProxyHandler({
            'http': '%s:%s' % (_proxy,_port),
            'https': '%s:%s' % (_proxy,_port)
        })
        opener = request.build_opener(proxy_handler)
        request.install_opener(opener)
        return
 
    #Unset Proxy
    def unset_proxy(self):
        proxy_handler = request.ProxyHandler({})
        opener = request.build_opener(proxy_handler)
        request.install_opener(opener)
        return
    
    #Encode URL Download
    def EncodeUrl(self,url):
        url = parse.urlsplit(url)
        url = list(url)
        url[2] = parse.quote(url[2])
        encoded_link = parse.urlunsplit(url)
        return encoded_link
    
    def download(self):
        """Dowload data funtion"""

        if self.dlg.comboBox_municipality.currentText() == '' or self.dlg.lineEdit_path.text() == '':
            self.not_data()

        else:

            try:
                
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                inecode_catastro = self.dlg.comboBox_municipality.currentText()
                codprov = inecode_catastro[0:2]
                codmuni = inecode_catastro[0:5]
                zippath = self.dlg.lineEdit_path.text()
    
                wd = os.path.join(zippath , inecode_catastro)
                
                proxy_support = urllib.request.ProxyHandler({})
                opener = urllib.request.build_opener(proxy_support)
                urllib.request.install_opener(opener)

                #Estabelcemos un proxy si lo ha definido el usuario
                try:
                    if (_proxy!= None and _proxy!= "") and (_port!= None and _port!= ""):
                        self.set_proxy()
                    else:
                        self.unset_proxy()
                except Exception as e:
                    QApplication.restoreOverrideCursor()
                    self.msgBar.pushMessage("Error estableciendo el proxy : "+ str(e) , level=QgsMessageBar.WARNING, duration=3)
                    raise
    
                # download de Cadastral Parcels
                if self.dlg.checkBox_parcels.isChecked():
    
                    url = u'http://www.catastro.minhap.es/INSPIRE/CadastralParcels/%s/%s/A.ES.SDGC.CP.%s.zip' % (
                        codprov , inecode_catastro , codmuni)
    
                    try:
                        os.makedirs(wd)
                    except OSError:
                        pass
    
                    zipParcels = os.path.join(wd , "%s_Parcels.zip" % inecode_catastro)  # poner fecha
    

                    e_url=self.EncodeUrl(url)
                    try:
                        urllib.request.urlretrieve(e_url , zipParcels, self.reporthook)
                    except:
                        shutil.rmtree(wd)
                        raise
    
                # download de Buildings
                if self.dlg.checkBox_buildings.isChecked():
    
                    url = u'http://www.catastro.minhap.es/INSPIRE/Buildings/%s/%s/A.ES.SDGC.BU.%s.zip' % (
                        codprov , inecode_catastro , codmuni)
    
                    try:
                        os.makedirs(wd)
                    except OSError:
                        pass
    
                    zipbuildings = os.path.join(wd , "%s_Buildings.zip" % inecode_catastro)  # poner fecha
                    
                    e_url=self.EncodeUrl(url)
                    
                    try:
                        urllib.request.urlretrieve(e_url , zipbuildings, self.reporthook)
                    except:
                        shutil.rmtree(wd)
                        raise
    
                # download de Addresses
                if self.dlg.checkBox_addresses.isChecked():
    
                    url = u'http://www.catastro.minhap.es/INSPIRE/Addresses/%s/%s/A.ES.SDGC.AD.%s.zip' % (
                        codprov , inecode_catastro , codmuni)
    
                    try:
                        os.makedirs(wd)
                    except OSError:
                        pass
    
                    zipAddresses = os.path.join(wd , "%s_Addresses.zip" % inecode_catastro)  # poner fecha
                    
                    e_url=self.EncodeUrl(url)
                    
                    try:
                        urllib.request.urlretrieve(e_url , zipAddresses, self.reporthook)
                    except:
                        shutil.rmtree(wd)
                        raise
    
                self.msgBar.pushMessage("Finished!" , level=QgsMessageBar.SUCCESS, duration=3)
                self.dlg.progressBar.setValue(100)#No llega al 100% aunque lo descargue,es random
                QApplication.restoreOverrideCursor()
                
                if self.dlg.checkBox_load_layers.isChecked():
                    try:
                        ## Descomprime los zips
                        self.msgBar.pushMessage("Start loading GML files..." , level=QgsMessageBar.INFO, duration=3)

                        for zipfilecatastro in os.listdir(wd):
                            if zipfilecatastro.endswith('.zip'):
                                with zipfile.ZipFile(os.path.join(wd , zipfilecatastro) , "r") as z:
                                    z.extractall(wd)
            
                        ## Carga los GMLs
                        for gmlfile in os.listdir(wd):
                            if gmlfile.endswith('.gml'):
                                layer = self.iface.addVectorLayer(os.path.join(wd , gmlfile) , "" ,
                                                             "ogr")
                                
                        self.msgBar.pushMessage("fichero descomprimido correctamente." , level=QgsMessageBar.INFO, duration=3)
                        
                    except:
                        self.msgBar.pushMessage("Error descomprimiendo el fichero." , level=QgsMessageBar.WARNING, duration=3)
                        QApplication.restoreOverrideCursor()
                        
                QApplication.restoreOverrideCursor()
                
            except Exception as e:
                QApplication.restoreOverrideCursor()
                self.msgBar.pushMessage("Failed! "+ str(e) , level=QgsMessageBar.WARNING, duration=3)
                return
                

    def run(self):
        """Run method that performs all the real work"""

        self.dlg.lineEdit_path.clear()

        self.dlg.comboBox_province.clear()
        self.dlg.comboBox_municipality.clear()
        self.dlg.comboBox_province.addItems(listProvincias)
        self.dlg.comboBox_province.currentIndexChanged.connect(self.filter_municipality)

        self.dlg.checkBox_parcels.setChecked(0)
        self.dlg.checkBox_buildings.setChecked(0)
        self.dlg.checkBox_addresses.setChecked(0)

        # show the dialog
        self.dlg.progressBar.setValue(0)
        self.dlg.setWindowIcon(QIcon (':/plugins/Spanish_Inspire_Catastral_Downloader/icon.png')); 
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:pass