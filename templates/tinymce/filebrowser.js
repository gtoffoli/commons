function djangoFileBrowser(input_id, input_value, type, win){
          var cmsURL = '/admin/filebrowser/browse/?pop=4';
          cmsURL = cmsURL + '&type=' + type;
          tinymce.activeEditor.windowManager.open({
            file: cmsURL,
            width: 800,  // Your dimensions may differ - toy around with them!
            height: 600,
            resizable: 'yes',
            scrollbars: 'yes',
            inline: 'no',  // This parameter only has an effect if you use the inlinepopups plugin!
            close_previous: 'no'
          }, {
            window: win,
            input: input_id,
          });
          return false;
}