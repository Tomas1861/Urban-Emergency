import { defineStore } from "pinia";
import { listRoles } from "../api/roles";

export const useAppStore = defineStore("app", {
  state: () => ({
    roles: [],
    rolesLoaded: false,
  }),
  actions: {
    async ensureRoles() {
      if (this.rolesLoaded) return this.roles;
      this.roles = await listRoles();
      this.rolesLoaded = true;
      return this.roles;
    },
    roleName(roleId) {
      return this.roles.find((r) => r.id === roleId)?.role_name || roleId;
    },
  },
});
