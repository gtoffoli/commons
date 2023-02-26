// https://vuejsexamples.com/a-prettier-way-to-display-select-boxes/
// https://stackoverflow.com/questions/47785382/convert-single-file-vue-components-to-javascript
// https://fluxfx.nl/htools/vue-conv#/

// component my-component
// Vue.component("dropdown", {
export default
{
	name: 'dropdown',
	type: 'module',
    template: `
    <div class="btn-group">
        <li v-on:click="toggleMenu()" class="dropdown-toggle" v-if="selectedOption.name !== undefined">
          {{ selectedOption.name }} - {{ selectedOption.start_date }}
          <span class="caret"></span>
        </li>

        <li v-on:click="toggleMenu()" class="dropdown-toggle dropdown-toggle-placeholder" v-if="selectedOption.name === undefined">
          {{placeholderText}}
          <span class="caret"></span>
        </li>

        <ul class="dropdown-menu" v-if="showMenu">
            <li v-for="(option, idx) in options" :key="idx">
                <a v-on:click="updateOption(option)">
                    {{ option.name }} - {{ option.start_date }}
                </a>
            </li>
        </ul>
    </div>
`,
    data() {
        return {
            selectedOption: {
                name: '',
            },
            showMenu: false,
            placeholderText: 'Please select an item',
        }
    },
    props: {
        options: {
            type: [Array, Object]
        },
        selected: {},
        placeholder: [String],
        closeOnOutsideClick: {
            type: [Boolean],
            default: false,
        },
    },

    mounted() {
        console.log('dropdown mounted 1', this.selected, this.placeholder, this.options, this.selectedOption)
        this.selectedOption = this.selected;
        if (this.placeholder) {
            this.placeholderText = this.placeholder;
        }

        if (this.closeOnOutsideClick) {
            document.addEventListener('click', this.clickHandler);
        }
        console.log('dropdown mounted 2', this.selectedOption, this.placeholder, this.options, this.selectedOption)
    },

    beforeDestroy() {
        document.removeEventListener('click', this.clickHandler);
    },

    methods: {
        updateOption(option) {
            this.selectedOption = option;
            this.showMenu = false;
            this.$emit('update-option', this.selectedOption);
        },

        toggleMenu() {
            this.showMenu = !this.showMenu;
        },

        clickHandler(event) {
            const {
                target
            } = event;
            const {
                $el
            } = this;

            if (!$el.contains(target)) {
                this.showMenu = false;
            }
        },
    }

};
